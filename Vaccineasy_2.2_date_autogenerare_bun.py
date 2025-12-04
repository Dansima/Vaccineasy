import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random
import io

# --- CONFIGURARE PAGINĂ ---
st.set_page_config(page_title="Cabinet Vaccinări V2", layout="wide")


# --- 1. LOGICA DE BUSINESS (BACKEND) ---

def decode_cnp(cnp):
    """Extrage data nașterii din CNP."""
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
        an = secol + aa
        return datetime(an, ll, zz)
    except:
        return None


def format_varsta(data_nasterii):
    """Calculează vârsta în format 'X ani, Y luni'."""
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
    """
    Motorul de Logică - Mapat pe Catagrafie
    """
    azi = datetime.now()
    varsta_zile = (azi - data_nasterii).days

    # Definim tintele si categoriile din Catagrafie
    tinte = {
        60: ("Hexavalent (2 luni)", "Hexa_2"),
        120: ("Hexavalent (4 luni)", "Hexa_4"),
        330: ("Hexavalent (11 luni)", "Hexa_11"),
        365: ("ROR (12 luni)", "ROR_12"),
        1825: ("ROR + Tetra (5 ani)", "ROR_Tetra_5"),
        5110: ("dTPa (14 ani)", "dTPa_14")
    }

    for zi_tinta, (nume_vaccin, cod_cat) in tinte.items():
        # Viitor apropiat (14 zile) - VERDE
        if 0 < (zi_tinta - varsta_zile) <= 14:
            return "🟢 Urmează", nume_vaccin, cod_cat

        # Scadent (Luna curenta) - GALBEN
        if 0 <= (varsta_zile - zi_tinta) <= 30:
            return "🟡 Scadent", nume_vaccin, cod_cat

        # Restant (A trecut luna) - ROSU
        if (varsta_zile - zi_tinta) > 30 and (varsta_zile - zi_tinta) < 200:
            return "🔴 RESTANT", nume_vaccin, cod_cat

    return "🟢 La Zi", "-", None


# --- 2. GENERATOR DE DATE FICTIVE ---
# --- 2. GENERATOR DE DATE FICTIVE (CALIBRAT) ---
@st.cache_data
def genereaza_pacienti(n=100):
    nume_lista = ["Popescu", "Ionescu", "Radu", "Dumitru", "Stan", "Stoica", "Gheorghe", "Dinu", "Serban", "Matei"]
    prenume_lista = ["Andrei", "Maria", "Elena", "Ionut", "Alex", "Sofia", "David", "Ana", "Gabriel", "Ioana"]

    data = []
    azi = datetime.now()

    # FORȚĂM CÂTEVA CAZURI SPECIFICE CA SĂ AVEM DATE ÎN TABEL
    # Generăm manual 10 cazuri de "Scadenți" (Galben) și "Urmează" (Verde)
    cazuri_fixe = [
        60, 65,  # 2 luni (scadenti)
        120, 130,  # 4 luni (scadenti)
        360,  # 1 an fara 5 zile (urmeaza)
        370,  # 1 an si 5 zile (scadent)
        5000,  # 13 ani si ceva
        55,  # Aproape 2 luni (urmeaza)
    ]

    for i in range(n):
        # Pentru primii 8 pacienti, folosim cazurile fixe sa fim siguri ca avem culori
        if i < len(cazuri_fixe):
            zile_random = cazuri_fixe[i]
        else:
            # Restul random
            zile_random = random.randint(30, 5500)

        data_nasterii = azi - timedelta(days=zile_random)

        an = str(data_nasterii.year)[-2:]
        luna = f"{data_nasterii.month:02d}"
        zi = f"{data_nasterii.day:02d}"
        sex = "5" if data_nasterii.year >= 2000 else "1"
        cnp = f"{sex}{an}{luna}{zi}123456"

        status_txt, vaccin, cod_cat = get_status_vaccinare(data_nasterii)

        # Mai putini restanțieri forțați, ca să vedem și galbenul
        if random.random() < 0.10 and i > 10:
            status_txt, vaccin, cod_cat = "🔴 RESTANT", "ROR (12 luni)", "ROR_12"

        data.append({
            "Nume": random.choice(nume_lista),
            "Prenume": random.choice(prenume_lista),
            "CNP": cnp,
            "Data Nașterii": data_nasterii,
            "Vârsta": format_varsta(data_nasterii),
            "Vaccin Necesar": vaccin,
            "Status": status_txt,
            "_cod_cat": cod_cat
        })
    return pd.DataFrame(data)


# --- 3. GENERATOR EXCEL (DESIGN IDENTIC CU ANEXA 1) ---
def convert_df_to_catagrafie(df_input):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('Anexa 1')

        # --- DEFINIRE STILURI (FORMATĂRI) ---
        # Stil pentru textul de sus (Unitatea sanitara etc.)
        fmt_top_left = workbook.add_format({'bold': False, 'align': 'left', 'font_size': 10})

        # Stil pentru Titlul Mare
        fmt_title = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 11})

        # Stiluri pentru Antet Tabel
        fmt_header_main = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True, 'font_size': 9
        })
        fmt_header_sub = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 9
        })
        fmt_vertical = workbook.add_format({
            'bold': False, 'align': 'center', 'valign': 'vcenter', 'border': 1,
            'rotation': 90, 'font_size': 8  # Text rotit vertical
        })

        # Stiluri pentru Date
        fmt_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10})
        fmt_left = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'border': 1, 'font_size': 10})
        fmt_bold_border = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})

        # --- 1. DESENARE ANTET DOCUMENT (Linii 1-4) ---
        worksheet.write('A1', 'Unitatea sanitară ...................................', fmt_top_left)
        worksheet.write('A2', 'Nr. .................... din ........................', fmt_top_left)

        # Titlul centrat pe lățimea tabelului (aprox 25 coloane)
        worksheet.merge_range('A4:Y4', 'Catagrafia copiilor conform calendarului naţional de vaccinare', fmt_title)
        worksheet.merge_range('A5:Y5', 'în luna .................... / anul 2025', fmt_title)

        # --- 2. CONFIGURARE COLOANE (Lățimi) ---
        worksheet.set_column(0, 0, 4)  # Nr Crt
        worksheet.set_column(1, 1, 30)  # Nume
        worksheet.set_column(2, 2, 15)  # CNP
        worksheet.set_column(3, 24, 3.5)  # Coloanele de vaccinuri (înguste)

        # --- 3. CONSTRUIRE TABEL (HEADER COMPLEX) ---
        # Randul de start pentru tabel este 6 (index 5)
        r_start = 6

        # Setăm înălțimea rândurilor din header
        worksheet.set_row(r_start, 40)  # Vaccinuri
        worksheet.set_row(r_start + 1, 20)  # Vârste
        worksheet.set_row(r_start + 2, 100)  # Verticale (Lot/Rest)

        # A. Coloanele Fixe (Nr, Nume, CNP) - Merge pe 3 rânduri
        worksheet.merge_range(r_start, 0, r_start + 2, 0, 'Nr.\nCrt.', fmt_header_main)
        worksheet.merge_range(r_start, 1, r_start + 2, 1, 'Numele şi prenumele', fmt_header_main)
        worksheet.merge_range(r_start, 2, r_start + 2, 2, 'CNP', fmt_header_main)

        # B. DTPa-VPI-Hib-HB (Hexa) - Coloane 3-8 (D-I)
        worksheet.merge_range(r_start, 3, r_start, 8, 'DTPa-VPI-Hib-HB', fmt_header_main)
        worksheet.merge_range(r_start + 1, 3, r_start + 1, 4, '2 luni', fmt_header_sub)
        worksheet.merge_range(r_start + 1, 5, r_start + 1, 6, '4 luni', fmt_header_sub)
        worksheet.merge_range(r_start + 1, 7, r_start + 1, 8, '11 luni', fmt_header_sub)

        # C. Pneumococic - Coloane 9-14 (J-O)
        worksheet.merge_range(r_start, 9, r_start, 14, 'Vaccin pneumococic\nconjugat', fmt_header_main)
        worksheet.merge_range(r_start + 1, 9, r_start + 1, 10, '2 luni', fmt_header_sub)
        worksheet.merge_range(r_start + 1, 11, r_start + 1, 12, '4 luni', fmt_header_sub)
        worksheet.merge_range(r_start + 1, 13, r_start + 1, 14, '11 luni', fmt_header_sub)

        # D. ROR - Coloane 15-18 (P-S)
        worksheet.merge_range(r_start, 15, r_start, 18, 'ROR', fmt_header_main)
        worksheet.merge_range(r_start + 1, 15, r_start + 1, 16, '12 luni', fmt_header_sub)
        worksheet.merge_range(r_start + 1, 17, r_start + 1, 18, '5 ani', fmt_header_sub)

        # E. DTPa-VPI (Tetra) - Coloane 19-20 (T-U)
        worksheet.merge_range(r_start, 19, r_start, 20, 'DTPa-\nVPI', fmt_header_main)
        worksheet.merge_range(r_start + 1, 19, r_start + 1, 20, '5-6 ani', fmt_header_sub)

        # F. dTPa (Adult) - Coloane 21-22 (V-W)
        worksheet.merge_range(r_start, 21, r_start, 22, 'dTPa', fmt_header_main)
        worksheet.merge_range(r_start + 1, 21, r_start + 1, 22, '14 ani', fmt_header_sub)

        # G. BCG si Hep B - Coloane 23-24 (X-Y) - Doar restantieri
        worksheet.merge_range(r_start, 23, r_start + 1, 23, 'BCG', fmt_header_main)
        worksheet.merge_range(r_start, 24, r_start + 1, 24, 'Hep B', fmt_header_main)

        # H. Sub-header vertical (Lot baza / Restantieri)
        # Scriem bucla pentru coloanele 3 pana la 22
        col_idx = 3
        while col_idx <= 22:
            worksheet.write(r_start + 2, col_idx, 'lot de baza', fmt_vertical)
            worksheet.write(r_start + 2, col_idx + 1, 'restantieri', fmt_vertical)
            col_idx += 2

        # Scriem manual pentru BCG si Hep B (doar restantieri)
        worksheet.write(r_start + 2, 23, 'restantieri', fmt_vertical)
        worksheet.write(r_start + 2, 24, 'restantieri', fmt_vertical)

        # --- 4. POPULARE CU DATE ---
        # Mapare logică cod_cat -> index coloană Excel (0-based)
        # A=0, B=1, C=2 ... D=3 ...
        col_map = {
            'Hexa_2': 3,  # D
            'Hexa_4': 5,  # F
            'Hexa_11': 7,  # H
            'ROR_12': 15,  # P
            'ROR_Tetra_5': [17, 19],  # R (ROR 5 ani) + T (Tetra 6 ani)
            'dTPa_14': 21  # V
        }

        current_row = r_start + 3
        nr_crt = 1

        for _, row in df_input.iterrows():
            # Excludem copiii care sunt "La Zi" sau "Urmează" (ei nu apar pe lista de consum/restante)
            if "La Zi" in row['Status'] or "Urmează" in row['Status']:
                continue

            # Scriem datele de identificare
            worksheet.write(current_row, 0, nr_crt, fmt_center)
            worksheet.write(current_row, 1, f"{row['Nume']} {row['Prenume']}", fmt_left)
            worksheet.write(current_row, 2, row['CNP'], fmt_center)

            # Identificam unde punem X
            cat = row['_cod_cat']
            is_restant = "RESTANT" in row['Status']
            offset = 1 if is_restant else 0

            if cat in col_map:
                cols = col_map[cat]
                if not isinstance(cols, list): cols = [cols]

                for c in cols:
                    # Punem X la coloana tinta
                    worksheet.write(current_row, c + offset, 'X', fmt_center)

                    # Logica Pneumo: daca e Hexa, punem automat X si la Pneumo (+6 coloane distanță)
                    if 3 <= c <= 8:
                        worksheet.write(current_row, c + 6 + offset, 'X', fmt_center)

            # Umplem restul celulelor goale cu border ca sa arate frumos
            for c in range(3, 25):
                # Putem scrie un string gol doar daca celula nu a fost scrisa deja
                # (xlsxwriter nu are functie de check, dar suprascrierea cu X s-a facut mai sus)
                # Daca vrem grid complet, putem aplica format pe range la final, dar e mai simplu linie cu linie aici
                pass

            current_row += 1
            nr_crt += 1

        # --- 5. FOOTER (Totaluri si Nota) ---
        worksheet.write(current_row, 1, 'TOTAL', fmt_bold_border)
        # Aplicam border la linia de total
        for c in range(2, 25):
            worksheet.write(current_row, c, '', fmt_center)

        current_row += 1
        worksheet.write(current_row, 1, 'TOTAL GENERAL', fmt_bold_border)
        # Aplicam border la linia de total general
        for c in range(2, 25):
            worksheet.write(current_row, c, '', fmt_center)

        current_row += 2
        worksheet.write(current_row, 0,
                        'NOTĂ: Catagrafia se păstrează la nivelul cabinetului medical/unităţii sanitare pentru a fi prezentată în vederea unor eventuale verificări.',
                        fmt_top_left)

        # Freeze Panes (Primele 3 coloane si primele 9 randuri inghetate)
        worksheet.freeze_panes(r_start + 3, 3)

    return output.getvalue()
# --- 4. INTERFAȚA GRAFICĂ ---

st.title("💉 Sistem Management Vaccinări - V2.1")
st.markdown("### 📋 Vizualizare și Raportare Catagrafie")

# Generam datele
df = genereaza_pacienti(100)

# Statistici
c1, c2, c3 = st.columns(3)
c1.metric("Total Pacienți", len(df))
c2.metric("Scadenți (Lot Bază)", len(df[df["Status"] == "🟡 Scadent"]))
c3.metric("Restanțieri", len(df[df["Status"] == "🔴 RESTANT"]))

# --- BUTON EXPORT EXCEL ---
st.markdown("---")
col_dwn, col_info = st.columns([1, 3])
with col_dwn:
    excel_data = convert_df_to_catagrafie(df)
    st.download_button(
        label="📥 Descarcă Catagrafie (.xlsx)",
        data=excel_data,
        file_name='catagrafie_luna_curenta.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        type="primary"
    )
with col_info:
    st.info(
        "💡 Apasă butonul pentru a genera raportul în formatul oficial (Hexa, Pneumo, ROR, pe loturi și restanțieri).")

# Tabelul Principal Vizual
st.subheader("Lista Operativă (Vizualizare Rapidă)")

filtru_status = st.multiselect(
    "Filtrează lista:",
    options=["🔴 RESTANT", "🟡 Scadent", "🟢 La Zi", "🟢 Urmează"],
    default=["🔴 RESTANT", "🟡 Scadent"]
)

if filtru_status:
    df_afisat = df[df["Status"].isin(filtru_status)]
else:
    df_afisat = df


# Functie Colorare
def highlight_rows(row):
    status = row['Status']

    if "RESTANT" in status:
        color = '#ff4b4b'  # Rosu
    elif "Scadent" in status:
        color = '#ffa421'  # Galben
    elif "Urmează" in status:
        color = '#21c354'  # Verde
    else:
        color = 'transparent'

    return [f'background-color: {color}; color: white; font-weight: bold' if col == 'Status' else '' for col in
            row.index]


cols_to_show = ["Nume", "Prenume", "CNP", "Vârsta", "Vaccin Necesar", "Status"]

st.dataframe(
    df_afisat[cols_to_show].style.apply(highlight_rows, axis=1),
    use_container_width=True,
    height=500
)