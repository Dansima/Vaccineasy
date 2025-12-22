import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Vaccineasy V3.2 (Paginare)", layout="wide")


# ==========================================
# 1. LOGICA DE BUSINESS (BACKEND)
# ==========================================

def decode_cnp(cnp):
    cnp = str(cnp).strip()
    cnp = ''.join(filter(str.isdigit, cnp))
    if len(cnp) < 13: return None
    try:
        s = int(cnp[0])
        aa = int(cnp[1:3])
        ll = int(cnp[3:5])
        zz = int(cnp[5:7])
        secol = 0
        if s in [1, 2]:
            secol = 1900
        elif s in [5, 6]:
            secol = 2000
        elif s in [3, 4]:
            secol = 1800
        an = secol + aa
        return datetime(an, ll, zz)
    except:
        return None


def format_varsta(data_nasterii):
    if not data_nasterii: return "CNP Invalid"
    azi = datetime.now()
    ani = azi.year - data_nasterii.year
    luni = azi.month - data_nasterii.month
    if luni < 0:
        ani -= 1
        luni += 12
    if ani == 0:
        return f"{luni} luni"
    elif luni == 0:
        return f"{ani} ani fix"
    else:
        return f"{ani} ani, {luni} luni"


def get_status_vaccinare(data_nasterii):
    if not data_nasterii: return "Eroare CNP", "-", None

    azi = datetime.now()
    varsta_zile = (azi - data_nasterii).days
    varsta_ani = varsta_zile / 365.25

    # FILTRU ADULȚI
    if varsta_ani > 15:
        return "🟢 Adult (Ignorat)", "-", None

    # Schema Națională
    tinte = {
        60: ("Hexavalent (2 luni)", "Hexa_2"),
        120: ("Hexavalent (4 luni)", "Hexa_4"),
        330: ("Hexavalent (11 luni)", "Hexa_11"),
        365: ("ROR (12 luni)", "ROR_12"),
        1825: ("ROR + Tetra (5 ani)", "ROR_Tetra_5"),
        5110: ("dTPa (14 ani)", "dTPa_14")
    }

    for zi_tinta, (nume_vaccin, cod_cat) in tinte.items():
        if 0 < (zi_tinta - varsta_zile) <= 14:
            return "🟢 Urmează", nume_vaccin, cod_cat
        if 0 <= (varsta_zile - zi_tinta) <= 30:
            return "🟡 Scadent", nume_vaccin, cod_cat
        if (varsta_zile - zi_tinta) > 30 and (varsta_zile - zi_tinta) < 500:
            return "🔴 RESTANT", nume_vaccin, cod_cat

    return "🟢 La Zi", "-", None


def incarca_date_din_excel(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file)
                if len(df.columns) < 2:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=';')
            except:
                st.error("Eroare CSV.")
                return pd.DataFrame()
        else:
            df = pd.read_excel(uploaded_file)

        df.columns = [str(c).lower().strip() for c in df.columns]
        col_nume = next((c for c in df.columns if 'nume' in c), None)
        col_cnp = next((c for c in df.columns if 'cnp' in c), None)

        if not col_nume or not col_cnp:
            st.error("Lipsesc coloanele Nume sau CNP.")
            return pd.DataFrame()

        processed_data = []
        for index, row in df.iterrows():
            cnp = str(row[col_cnp]).strip()
            nume = str(row[col_nume]).strip()
            dn = decode_cnp(cnp)
            status, vaccin, cod_cat = get_status_vaccinare(dn)

            if "Adult" in status or "Eroare" in status: continue

            processed_data.append({
                "Nume si Prenume": nume,
                "CNP": cnp,
                "Vârsta": format_varsta(dn),
                "Vaccin Necesar": vaccin,
                "Status": status,
                "_cod_cat": cod_cat
            })
        return pd.DataFrame(processed_data)
    except Exception as e:
        st.error(f"Eroare fișier: {e}")
        return pd.DataFrame()


# ==========================================
# 2. GENERATOR EXCEL - PAGINAT (13 Linii/Pagina)
# ==========================================
def convert_df_to_catagrafie(df_input):
    output = io.BytesIO()

    # 1. Filtram doar datele relevante pentru export
    # (Excludem 'La Zi' și 'Urmează' - exportăm doar ce trebuie raportat: Scadent/Restant)
    # Dacă vrei să apară și 'Urmează', scoate condiția de mai jos.
    df_export = df_input[~df_input['Status'].isin(["🟢 La Zi", "🟢 Urmează"])].copy()

    # 2. Împărțim în chunks de 13
    LIMITA_PAGINA = 13
    chunks = [df_export[i:i + LIMITA_PAGINA] for i in range(0, len(df_export), LIMITA_PAGINA)]

    if not chunks:  # Daca e gol, facem un chunk gol ca sa nu crape
        chunks = [pd.DataFrame(columns=df_input.columns)]

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book

        # Definire Stiluri (O singură dată)
        fmt_top_left = workbook.add_format({'bold': False, 'align': 'left', 'font_size': 10})
        fmt_title = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 11})
        fmt_header_main = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'font_size': 9})
        fmt_header_sub = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 9})
        fmt_vertical = workbook.add_format(
            {'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'rotation': 90, 'font_size': 8})
        fmt_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10})
        fmt_left = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'border': 1, 'font_size': 10})
        fmt_bold_border = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})

        # --- LOOP PENTRU FIECARE PAGINĂ ---
        for i, chunk in enumerate(chunks):
            sheet_name = f'Pagina {i + 1}'
            worksheet = workbook.add_worksheet(sheet_name)

            # --- DESENARE HEADER (Identic pe fiecare pagină) ---
            worksheet.write('A1', 'Unitatea sanitară ...................................', fmt_top_left)
            worksheet.write('A2', 'Nr. .................... din ........................', fmt_top_left)
            worksheet.merge_range('A4:Y4', 'Catagrafia copiilor conform calendarului naţional de vaccinare', fmt_title)
            worksheet.merge_range('A5:Y5',
                                  f'în luna {datetime.now().month} / anul {datetime.now().year} - Pagina {i + 1}',
                                  fmt_title)

            worksheet.set_column(0, 0, 4)
            worksheet.set_column(1, 1, 30)
            worksheet.set_column(2, 2, 15)
            worksheet.set_column(3, 24, 3.5)

            r_start = 6
            worksheet.set_row(r_start, 40)
            worksheet.set_row(r_start + 1, 20)
            worksheet.set_row(r_start + 2, 100)

            worksheet.merge_range(r_start, 0, r_start + 2, 0, 'Nr.\nCrt.', fmt_header_main)
            worksheet.merge_range(r_start, 1, r_start + 2, 1, 'Numele şi prenumele', fmt_header_main)
            worksheet.merge_range(r_start, 2, r_start + 2, 2, 'CNP', fmt_header_main)

            # Vaccinuri Headers
            worksheet.merge_range(r_start, 3, r_start, 8, 'DTPa-VPI-Hib-HB', fmt_header_main)
            worksheet.merge_range(r_start + 1, 3, r_start + 1, 4, '2 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 5, r_start + 1, 6, '4 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 7, r_start + 1, 8, '11 luni', fmt_header_sub)

            worksheet.merge_range(r_start, 9, r_start, 14, 'Vaccin pneumococic\nconjugat', fmt_header_main)
            worksheet.merge_range(r_start + 1, 9, r_start + 1, 10, '2 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 11, r_start + 1, 12, '4 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 13, r_start + 1, 14, '11 luni', fmt_header_sub)

            worksheet.merge_range(r_start, 15, r_start, 18, 'ROR', fmt_header_main)
            worksheet.merge_range(r_start + 1, 15, r_start + 1, 16, '12 luni', fmt_header_sub)
            worksheet.merge_range(r_start + 1, 17, r_start + 1, 18, '5 ani', fmt_header_sub)

            worksheet.merge_range(r_start, 19, r_start, 20, 'DTPa-\nVPI', fmt_header_main)
            worksheet.merge_range(r_start + 1, 19, r_start + 1, 20, '5-6 ani', fmt_header_sub)

            worksheet.merge_range(r_start, 21, r_start, 22, 'dTPa', fmt_header_main)
            worksheet.merge_range(r_start + 1, 21, r_start + 1, 22, '14 ani', fmt_header_sub)

            worksheet.merge_range(r_start, 23, r_start + 1, 23, 'BCG', fmt_header_main)
            worksheet.merge_range(r_start, 24, r_start + 1, 24, 'Hep B', fmt_header_main)

            col_idx = 3
            while col_idx <= 22:
                worksheet.write(r_start + 2, col_idx, 'lot de baza', fmt_vertical)
                worksheet.write(r_start + 2, col_idx + 1, 'restantieri', fmt_vertical)
                col_idx += 2
            worksheet.write(r_start + 2, 23, 'restantieri', fmt_vertical)
            worksheet.write(r_start + 2, 24, 'restantieri', fmt_vertical)

            # --- POPULARE DATE (Doar chunk-ul curent) ---
            col_map = {
                'Hexa_2': 3, 'Hexa_4': 5, 'Hexa_11': 7,
                'ROR_12': 15, 'ROR_Tetra_5': [17, 19], 'dTPa_14': 21
            }

            current_row = r_start + 3
            # Nr crt trebuie să continue corect (ex: Pag 2 incepe cu 14)
            nr_crt = (i * LIMITA_PAGINA) + 1

            for _, row in chunk.iterrows():
                worksheet.write(current_row, 0, nr_crt, fmt_center)
                worksheet.write(current_row, 1, row['Nume si Prenume'], fmt_left)
                worksheet.write(current_row, 2, row['CNP'], fmt_center)

                cat = row['_cod_cat']
                is_restant = "RESTANT" in row['Status']
                offset = 1 if is_restant else 0

                if cat in col_map:
                    cols = col_map[cat]
                    if not isinstance(cols, list): cols = [cols]
                    for c in cols:
                        worksheet.write(current_row, c + offset, 'X', fmt_center)
                        if 3 <= c <= 8:
                            worksheet.write(current_row, c + 6 + offset, 'X', fmt_center)

                # Border gol pe restul
                for c in range(3, 25): pass

                current_row += 1
                nr_crt += 1

            # --- FOOTER (Pe fiecare pagină sau doar la final) ---
            # De obicei semnătura e necesară pe fiecare pagină
            worksheet.write(current_row, 1, 'TOTAL', fmt_bold_border)
            current_row += 1
            worksheet.write(current_row, 1, 'TOTAL GENERAL', fmt_bold_border)
            current_row += 2
            worksheet.write(current_row, 0, 'NOTĂ: Pagină generată automat.', fmt_top_left)
            worksheet.freeze_panes(r_start + 3, 3)

    return output.getvalue()


# ==========================================
# 3. INTERFAȚA GRAFICĂ (V3.1 Style)
# ==========================================

st.title("💉 Sistem Vaccinări - V3.2 (Paginare Automată)")

with st.sidebar:
    st.header("1. Import Date")
    uploaded_file = st.file_uploader("Încarcă Excel/CSV din ICMED", type=['xlsx', 'xls', 'csv'])
    st.info("ℹ️ Aplicația acceptă fișiere .csv și .xlsx")

if uploaded_file is not None:
    if 'data_cache' not in st.session_state or st.session_state.uploaded_filename != uploaded_file.name:
        with st.spinner('Se procesează lista...'):
            df = incarca_date_din_excel(uploaded_file)
            st.session_state.data_cache = df
            st.session_state.uploaded_filename = uploaded_file.name
    else:
        df = st.session_state.data_cache

    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Pacienți Copii", len(df))
        c2.metric("De Vaccinat", len(df[df["Status"].str.contains("Scadent")]))
        c3.metric("Restanțieri", len(df[df["Status"].str.contains("RESTANT")]))

        st.markdown("---")

        # ZONA DE EXPORT
        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            excel_data = convert_df_to_catagrafie(df)
            st.download_button(
                "📥 Descarcă Anexa 1 (Paginată)",
                data=excel_data,
                file_name=f'Catagrafie_Paginata_{datetime.now().strftime("%B_%Y")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                type="primary"
            )
        with col_info:
            st.info("💡 Exportul va genera automat mai multe foi (Sheet-uri) în Excel dacă ai mai mult de 13 copii.")

        st.subheader("Lista Operativă")
        optiuni_filtru = ["🔴 RESTANT", "🟡 Scadent", "🟢 Urmează", "🟢 La Zi"]
        filtru = st.multiselect("Filtrează:", optiuni_filtru, default=["🔴 RESTANT", "🟡 Scadent"])

        mask = df['Status'].apply(lambda x: any(f in x for f in filtru))
        df_afisat = df[mask]


        def highlight_rows(row):
            status = row['Status']
            if "RESTANT" in status:
                color = '#ff4b4b'
            elif "Scadent" in status:
                color = '#ffa421'
            elif "Urmează" in status:
                color = '#21c354'
            else:
                color = 'transparent'
            return [f'background-color: {color}; color: white; font-weight: bold' if col == 'Status' else '' for col in
                    row.index]


        cols_show = ["Nume si Prenume", "CNP", "Vârsta", "Vaccin Necesar", "Status"]
        st.dataframe(df_afisat[cols_show].style.apply(highlight_rows, axis=1), use_container_width=True, height=600)
    else:
        st.warning("Nu s-au găsit date valide în fișier.")
else:
    st.markdown("### 👋 Încarcă fișierul pentru a începe.")