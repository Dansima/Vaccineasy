"""
Vaccineasy v4.0 — Excel Exporter (Catagrafie / Anexa 1)
Generates the official vaccination report with pagination (13 rows/page).
"""

import io
from collections import Counter
from datetime import datetime
from typing import Optional

import pandas as pd
from xlsxwriter.utility import xl_col_to_name
from app.reporting import filter_monthly_report

COL_MAP = {'Hexa_2': 3, 'Hexa_4': 5, 'Hexa_11': 7,
           'ROR_12': 15, 'ROR_Tetra_5': 17, 'Tetra_6': 19, 'dTPa_14': 21}


def _marked_columns(row):
    pending = row.get('_pending')
    if not isinstance(pending, list):
        codes = row.get('_all_codes')
        if not isinstance(codes, list):
            codes = [row['_cod_cat']] if row.get('_cod_cat') else []
        pending = [(row['Status'], '', code) for code in codes]
    marked = set()
    for status, _, code in pending:
        if code in COL_MAP:
            col = COL_MAP[code] + int('RESTANT' in status)
            marked.add(col)
            if code.startswith('Hexa_'):
                marked.add(col + 6)
    return marked


def convert_df_to_catagrafie(df_input: pd.DataFrame,
                              reference_date: Optional[datetime] = None) -> bytes:
    """
    Generate the official Anexa 1 Excel report with automatic pagination.
    Each sheet contains up to 13 patient rows.

    Args:
        df_input:       DataFrame with columns 'Nume si Prenume', 'CNP',
                        'Status', '_cod_cat', 'Vârsta_datetime'.
        reference_date: The "as-of" date used for the sheet title header
                        ("în luna X / anul Y"). Defaults to today when omitted.
    """
    output = io.BytesIO()
    ref = reference_date if reference_date is not None else datetime.now()

    # Filter: export out only "La Zi".
    # This means Scadent, Restant, AND Urmează (upcoming) are exported.
    if '_pending' in df_input.columns:
        df_export = filter_monthly_report(df_input, ref)
    else:
        df_export = df_input[~df_input['Status'].isin(["🟢 La Zi"])].copy()

    # Sort descending by Vârsta_datetime (youngest first = largest datetime)
    if 'Vârsta_datetime' in df_export.columns:
        df_export = df_export.sort_values(by='Vârsta_datetime', ascending=False)

    # Paginate: 13 rows per page
    LIMITA_PAGINA = 13
    chunks = [df_export[i:i + LIMITA_PAGINA] for i in range(0, len(df_export), LIMITA_PAGINA)]

    if not chunks:
        chunks = [pd.DataFrame(columns=df_input.columns)]

    total_counts = Counter(c for _, row in df_export.iterrows() for c in _marked_columns(row))

    with pd.ExcelWriter(output, engine='xlsxwriter', engine_kwargs={'options': {
            'strings_to_formulas': False, 'strings_to_urls': False}}) as writer:
        workbook = writer.book

        # --- Define Styles (once) ---
        fmt_top_left = workbook.add_format({
            'bold': False, 'align': 'left', 'font_size': 10
        })
        fmt_title = workbook.add_format({
            'bold': True, 'align': 'center', 'font_size': 11
        })
        fmt_header_main = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'border': 1, 'text_wrap': True, 'font_size': 9
        })
        fmt_header_sub = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'border': 1, 'font_size': 9
        })
        fmt_vertical = workbook.add_format({
            'bold': False, 'align': 'center', 'valign': 'vcenter',
            'border': 1, 'rotation': 90, 'font_size': 8
        })
        fmt_center = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10
        })
        fmt_left = workbook.add_format({
            'align': 'left', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'text_wrap': True
        })
        fmt_bold_border = workbook.add_format({
            'bold': True, 'border': 1, 'font_size': 10
        })
        fmt_empty_cell = workbook.add_format({
            'border': 1, 'font_size': 10
        })

        # --- Generate each page ---
        for i, chunk in enumerate(chunks):
            sheet_name = f'Pagina {i + 1}'
            worksheet = workbook.add_worksheet(sheet_name)
            worksheet.set_landscape()
            worksheet.set_paper(9)  # A4
            worksheet.fit_to_pages(1, 1)
            worksheet.set_margins(0.25, 0.25, 0.3, 0.3)
            worksheet.center_horizontally()

            # --- Document Header ---
            worksheet.write('A1', 'Unitatea sanitară ...................................', fmt_top_left)
            worksheet.write('A2', 'Nr. .................... din ........................', fmt_top_left)
            worksheet.merge_range('A4:Y4',
                                  'Catagrafia copiilor conform calendarului naţional de vaccinare',
                                  fmt_title)
            worksheet.merge_range('A5:Y5',
                                  f'în luna {ref.month} / anul {ref.year} - Pagina {i + 1}',
                                  fmt_title)

            # --- Column widths ---
            worksheet.set_column(0, 0, 4)      # Nr Crt
            worksheet.set_column(1, 1, 30)     # Nume
            worksheet.set_column(2, 2, 15)     # CNP
            worksheet.set_column(3, 24, 3.5)   # Vaccine columns

            # --- Table Header (3 rows) ---
            r_start = 6
            worksheet.set_row(r_start, 40)
            worksheet.set_row(r_start + 1, 20)
            worksheet.set_row(r_start + 2, 100)

            # Fixed columns
            worksheet.merge_range(r_start, 0, r_start + 2, 0, 'Nr.\nCrt.', fmt_header_main)
            worksheet.merge_range(r_start, 1, r_start + 2, 1, 'Numele şi prenumele', fmt_header_main)
            worksheet.merge_range(r_start, 2, r_start + 2, 2, 'CNP', fmt_header_main)

            # DTPa-VPI-Hib-HB (Hexavalent)
            worksheet.merge_range(r_start, 3, r_start, 8, 'DTPa-VPI-Hib-HB', fmt_header_main)
            worksheet.merge_range(r_start + 1, 3, r_start + 1, 4, '2 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 5, r_start + 1, 6, '4 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 7, r_start + 1, 8, '11 luni', fmt_header_sub)

            # Pneumococcal
            worksheet.merge_range(r_start, 9, r_start, 14, 'Vaccin pneumococic\nconjugat', fmt_header_main)
            worksheet.merge_range(r_start + 1, 9, r_start + 1, 10, '2 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 11, r_start + 1, 12, '4 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 13, r_start + 1, 14, '11 luni', fmt_header_sub)

            # ROR
            worksheet.merge_range(r_start, 15, r_start, 18, 'ROR', fmt_header_main)
            worksheet.merge_range(r_start + 1, 15, r_start + 1, 16, '12 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 17, r_start + 1, 18, '5 ani', fmt_header_sub)

            # DTPa-VPI (Tetra)
            worksheet.merge_range(r_start, 19, r_start, 20, 'DTPa-\nVPI', fmt_header_main)
            worksheet.merge_range(r_start + 1, 19, r_start + 1, 20, '5-6 ani', fmt_header_sub)

            # dTPa
            worksheet.merge_range(r_start, 21, r_start, 22, 'dTPa', fmt_header_main)
            worksheet.merge_range(r_start + 1, 21, r_start + 1, 22, '14 ani', fmt_header_sub)

            # BCG & Hep B
            worksheet.merge_range(r_start, 23, r_start + 1, 23, 'BCG', fmt_header_main)
            worksheet.merge_range(r_start, 24, r_start + 1, 24, 'Hep B', fmt_header_main)

            # Sub-headers (vertical: "lot de baza" / "restantieri")
            col_idx = 3
            while col_idx <= 22:
                worksheet.write(r_start + 2, col_idx, 'lot de baza', fmt_vertical)
                worksheet.write(r_start + 2, col_idx + 1, 'restantieri', fmt_vertical)
                col_idx += 2
            worksheet.write(r_start + 2, 23, 'restantieri', fmt_vertical)
            worksheet.write(r_start + 2, 24, 'restantieri', fmt_vertical)

            # --- Populate Data ---
            current_row = r_start + 3
            nr_crt = (i * LIMITA_PAGINA) + 1
            page_counts = Counter()

            for _, row in chunk.iterrows():
                worksheet.set_row(current_row, 30)
                worksheet.write(current_row, 0, nr_crt, fmt_center)
                worksheet.write_string(current_row, 1, str(row['Nume si Prenume']), fmt_left)
                worksheet.write_string(current_row, 2, str(row['CNP']), fmt_center)

                # Track which cells have been written to
                written_cols = _marked_columns(row)
                page_counts.update(written_cols)
                for col in written_cols:
                    worksheet.write(current_row, col, 'X', fmt_center)

                # Apply borders to empty cells
                for c in range(3, 25):
                    if c not in written_cols:
                        worksheet.write(current_row, c, '', fmt_empty_cell)

                current_row += 1
                nr_crt += 1

            # Reserve all 13 patient rows, including on the final page.
            while current_row < 22:
                worksheet.set_row(current_row, 30)
                for c in range(25):
                    worksheet.write_blank(current_row, c, None, fmt_empty_cell)
                current_row += 1

            # --- Footer ---
            worksheet.write_blank(current_row, 0, None, fmt_center)
            worksheet.write(current_row, 1, 'TOTAL', fmt_bold_border)
            worksheet.write(current_row, 2, len(chunk), fmt_center)
            for c in range(3, 25):
                col = xl_col_to_name(c)
                worksheet.write_formula(current_row, c, f'=COUNTIF({col}10:{col}22,"X")',
                                        fmt_center, page_counts[c])
            current_row += 1
            worksheet.write_blank(current_row, 0, None, fmt_center)
            worksheet.write(current_row, 1, 'TOTAL GENERAL', fmt_bold_border)
            worksheet.write_formula(current_row, 2,
                '=' + '+'.join(f"'Pagina {page + 1}'!C23" for page in range(len(chunks))),
                fmt_center, len(df_export))
            for c in range(3, 25):
                col = xl_col_to_name(c)
                worksheet.write_formula(current_row, c,
                    '=' + '+'.join(f"'Pagina {page + 1}'!{col}23" for page in range(len(chunks))),
                    fmt_center, total_counts[c])
            current_row += 2
            worksheet.merge_range(current_row, 0, current_row, 24,
                            'NOTĂ: Catagrafia se păstrează la nivelul cabinetului medical/unităţii sanitare '
                            'pentru a fi prezentată în vederea unor eventuale verificări.',
                            workbook.add_format({'font_size': 8, 'text_wrap': True, 'valign': 'top'}))
            worksheet.set_row(current_row, 28)
            worksheet.print_area(0, 0, current_row, 24)
            worksheet.freeze_panes(r_start + 3, 3)

    return output.getvalue()
