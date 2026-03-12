"""
Vaccineasy v4.0 — Excel Exporter (Catagrafie / Anexa 1)
Generates the official vaccination report with pagination (13 rows/page).
"""

import io
from datetime import datetime

import pandas as pd


def convert_df_to_catagrafie(df_input: pd.DataFrame) -> bytes:
    """
    Generate the official Anexa 1 Excel report with automatic pagination.
    Each sheet contains up to 13 patient rows.

    Expects df_input with columns:
        'Nume si Prenume', 'CNP', 'Status', '_cod_cat'
    """
    output = io.BytesIO()

    # Filter: export only Scadent and Restant
    df_export = df_input[~df_input['Status'].isin(["🟢 La Zi", "🟢 Urmează"])].copy()

    # Paginate: 13 rows per page
    LIMITA_PAGINA = 13
    chunks = [df_export[i:i + LIMITA_PAGINA] for i in range(0, len(df_export), LIMITA_PAGINA)]

    if not chunks:
        chunks = [pd.DataFrame(columns=df_input.columns)]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
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
            'align': 'left', 'valign': 'vcenter', 'border': 1, 'font_size': 10
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

            # --- Document Header ---
            worksheet.write('A1', 'Unitatea sanitară ...................................', fmt_top_left)
            worksheet.write('A2', 'Nr. .................... din ........................', fmt_top_left)
            worksheet.merge_range('A4:Y4',
                                  'Catagrafia copiilor conform calendarului naţional de vaccinare',
                                  fmt_title)
            worksheet.merge_range('A5:Y5',
                                  f'în luna {datetime.now().month} / anul {datetime.now().year} - Pagina {i + 1}',
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
            col_map = {
                'Hexa_2': 3, 'Hexa_4': 5, 'Hexa_11': 7,
                'ROR_12': 15, 'ROR_Tetra_5': [17, 19], 'dTPa_14': 21
            }

            current_row = r_start + 3
            nr_crt = (i * LIMITA_PAGINA) + 1

            for _, row in chunk.iterrows():
                worksheet.write(current_row, 0, nr_crt, fmt_center)
                worksheet.write(current_row, 1, row['Nume si Prenume'], fmt_left)
                worksheet.write(current_row, 2, row['CNP'], fmt_center)

                # Track which cells have been written to
                written_cols = {0, 1, 2}

                cat = row['_cod_cat']
                is_restant = "RESTANT" in row['Status']
                offset = 1 if is_restant else 0

                if cat in col_map:
                    cols = col_map[cat]
                    if not isinstance(cols, list):
                        cols = [cols]
                    for c in cols:
                        worksheet.write(current_row, c + offset, 'X', fmt_center)
                        written_cols.add(c + offset)
                        # Pneumococcal auto-fill for Hexavalent
                        if 3 <= c <= 8:
                            worksheet.write(current_row, c + 6 + offset, 'X', fmt_center)
                            written_cols.add(c + 6 + offset)

                # Bug #5 fix: actually apply borders to empty cells
                for c in range(3, 25):
                    if c not in written_cols:
                        worksheet.write(current_row, c, '', fmt_empty_cell)

                current_row += 1
                nr_crt += 1

            # --- Footer ---
            worksheet.write(current_row, 1, 'TOTAL', fmt_bold_border)
            for c in range(2, 25):
                worksheet.write(current_row, c, '', fmt_center)
            current_row += 1
            worksheet.write(current_row, 1, 'TOTAL GENERAL', fmt_bold_border)
            for c in range(2, 25):
                worksheet.write(current_row, c, '', fmt_center)
            current_row += 2
            worksheet.write(current_row, 0,
                            'NOTĂ: Catagrafia se păstrează la nivelul cabinetului medical/unităţii sanitare '
                            'pentru a fi prezentată în vederea unor eventuale verificări.',
                            fmt_top_left)
            worksheet.freeze_panes(r_start + 3, 3)

    return output.getvalue()
