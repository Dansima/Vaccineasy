"""
Vaccineasy v4.0 — Main Streamlit Application
Persistent vaccination management with SQLite database.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

from app.business_logic import (
    decode_cnp, format_varsta,
    get_all_vaccination_statuses, get_single_vaccination_status,
    VACCINATION_SCHEDULE
)
from app.database import (
    init_db, import_patients_from_excel,
    get_all_patients, get_children_patients,
    record_vaccination, get_vaccination_history,
    get_vaccinated_codes_for_patient, get_all_vaccines,
    get_db_stats, delete_vaccination_record
)
from app.excel_exporter import convert_df_to_catagrafie

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Vaccineasy V4.0",
    page_icon="💉",
    layout="wide"
)

# --- MODERN THEME CSS ---
st.markdown("""
<style>
    /* ===== Google Font ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ===== Global ===== */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* ===== Main container ===== */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* ===== Headers ===== */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.5px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.3px !important;
    }

    /* ===== Metric cards ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.7;
    }
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
    }

    /* ===== Sidebar ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        background: none !important;
        -webkit-text-fill-color: white !important;
    }

    /* ===== Tabs ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.2px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-bottom: none !important;
    }

    /* ===== Buttons ===== */
    .stButton > button[kind="primary"],
    .stDownloadButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.3px;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stDownloadButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5) !important;
    }

    /* ===== Dataframe ===== */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08);
    }

    /* ===== Inputs ===== */
    .stSelectbox, .stMultiSelect, .stTextInput, .stTextArea, .stDateInput {
        font-family: 'Inter', sans-serif !important;
    }
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    .stTextInput > div > div > input,
    .stTextArea > div > textarea {
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ===== Info/Success/Warning/Error boxes ===== */
    .stAlert {
        border-radius: 12px !important;
        border-left-width: 4px !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ===== File Uploader ===== */
    [data-testid="stFileUploader"] {
        border-radius: 12px;
    }

    /* ===== Dividers ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.3), transparent);
        margin: 1.5rem 0;
    }

    /* ===== Subtle animation on page load ===== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .main .block-container {
        animation: fadeInUp 0.4s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE DATABASE ---
init_db()


# =============================================================
# HELPER: Build the operative list from DB patients
# =============================================================
@st.cache_data(ttl=30)
def build_operative_list():
    """
    Build the operative patient list from the database.
    Returns a DataFrame with ONE ROW PER PATIENT.
    Vaccination statuses are consolidated: all pending vaccines listed together.
    """
    children = get_children_patients()

    if not children:
        return pd.DataFrame()

    rows = []
    for patient in children:
        dn = patient["data_nasterii"]

        # Get vaccines already administered
        vaccinated_codes = get_vaccinated_codes_for_patient(patient["id"])

        # Get all pending statuses
        all_statuses = get_all_vaccination_statuses(dn)

        if not all_statuses:
            rows.append({
                "ID": patient["id"],
                "Nume si Prenume": patient["nume"],
                "CNP": patient["cnp"],
                "Vârsta": format_varsta(dn),
                "Vaccin Necesar": "-",
                "Status": "🟢 La Zi",
                "_cod_cat": None,
                "_all_codes": [],
            })
            continue

        if any("Adult" in s[0] or "Eroare" in s[0] for s in all_statuses):
            continue

        # Filter out vaccines already administered
        pending = [(s, v, c) for s, v, c in all_statuses if c not in vaccinated_codes]

        if not pending:
            rows.append({
                "ID": patient["id"],
                "Nume si Prenume": patient["nume"],
                "CNP": patient["cnp"],
                "Vârsta": format_varsta(dn),
                "Vaccin Necesar": "-",
                "Status": "🟢 La Zi",
                "_cod_cat": None,
                "_all_codes": [],
            })
            continue

        # Consolidate: ONE row per patient with all pending vaccines
        vaccine_names = [v for _, v, _ in pending]
        vaccine_codes = [c for _, _, c in pending]

        # Determine worst status (priority: RESTANT > Scadent > Urmează)
        statuses = [s for s, _, _ in pending]
        if any("RESTANT" in s for s in statuses):
            worst_status = "🔴 RESTANT"
        elif any("Scadent" in s for s in statuses):
            worst_status = "🟡 Scadent"
        else:
            worst_status = "🟢 Urmează"

        rows.append({
            "ID": patient["id"],
            "Nume si Prenume": patient["nume"],
            "CNP": patient["cnp"],
            "Vârsta": format_varsta(dn),
            "Vaccin Necesar": ", ".join(vaccine_names),
            "Status": worst_status,
            "_cod_cat": vaccine_codes[0] if vaccine_codes else None,
            "_all_codes": vaccine_codes,
        })

    return pd.DataFrame(rows)


# =============================================================
# STYLING
# =============================================================
def highlight_rows(row):
    """Color-code rows by vaccination status."""
    status = row['Status']
    if "RESTANT" in status:
        bg = 'rgba(255, 75, 75, 0.25)'
        color = '#ff6b6b'
    elif "Scadent" in status:
        bg = 'rgba(255, 164, 33, 0.25)'
        color = '#ffc078'
    elif "Urmează" in status:
        bg = 'rgba(33, 195, 84, 0.25)'
        color = '#69db7c'
    else:
        bg = 'transparent'
        color = 'inherit'
    return [
        f'background-color: {bg}; color: {color}; font-weight: 700; border-radius: 6px;'
        if col == 'Status' else ''
        for col in row.index
    ]


# =============================================================
# SIDEBAR
# =============================================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="font-size: 3rem; margin-bottom: 0.3rem;">💉</div>
        <div style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Vaccineasy
        </div>
        <div style="font-size: 0.75rem; opacity: 0.5; margin-top: 2px; letter-spacing: 2px; text-transform: uppercase;">
            v4.0 · Bază de date locală
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Database stats
    stats = get_db_stats()
    st.metric("Pacienți în DB", stats["total_patients"])
    st.metric("Vaccinări Înregistrate", stats["total_vaccination_records"])

    st.markdown("---")

    # Excel Import Section
    st.markdown("##### 📁 Import Date")
    uploaded_file = st.file_uploader(
        "Încarcă Excel/CSV din ICMED",
        type=['xlsx', 'xls', 'csv'],
        help="Fișierul trebuie să conțină coloanele 'Nume' și 'CNP'"
    )
    if uploaded_file:
        if st.button("🔄 Importă în Baza de Date", type="primary", use_container_width=True):
            with st.spinner("Se importă datele..."):
                result = import_patients_from_excel(uploaded_file)
                st.cache_data.clear()

            if result["errors"]:
                for err in result["errors"]:
                    st.error(err)
            else:
                st.success(
                    f"✅ Import finalizat!\n\n"
                    f"- **Noi:** {result['imported']}\n"
                    f"- **Actualizați:** {result['updated']}\n"
                    f"- **Omise:** {result['skipped']}"
                )

    st.markdown("---")
    st.info("ℹ️ Datele sunt salvate local și persistă după repornirea containerului Docker.")


# =============================================================
# MAIN CONTENT — TABS
# =============================================================
st.title("💉 Vaccineasy")
st.caption("Sistem Management Vaccinări Pediatrice · Calendarul Național de Vaccinare")

tab_dashboard, tab_record, tab_history, tab_export = st.tabs([
    "📊 Dashboard", "💊 Înregistrare Vaccinare", "📋 Istoric Pacient", "📥 Export Anexa 1"
])


# ---- TAB 1: DASHBOARD ----
with tab_dashboard:
    df = build_operative_list()

    if df.empty:
        st.markdown("### 👋 Nu există pacienți în baza de date.")
        st.markdown("Încarcă un fișier Excel/CSV din bara laterală pentru a începe.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Copii Înregistrați", df["ID"].nunique())

        restant_count = len(df[df["Status"].str.contains("RESTANT", na=False)])
        scadent_count = len(df[df["Status"].str.contains("Scadent", na=False)])
        la_zi_count = len(df[df["Status"].str.contains("La Zi", na=False)])

        c2.metric("🔴 Restanțieri", restant_count)
        c3.metric("🟡 De Vaccinat", scadent_count)
        c4.metric("🟢 La Zi", la_zi_count)

        st.markdown("---")

        st.subheader("Lista Operativă")
        optiuni_filtru = ["🔴 RESTANT", "🟡 Scadent", "🟢 Urmează", "🟢 La Zi"]
        filtru = st.multiselect(
            "Filtrează după status:",
            optiuni_filtru,
            default=["🔴 RESTANT", "🟡 Scadent"]
        )

        mask = df['Status'].apply(lambda x: any(f in x for f in filtru))
        df_afisat = df[mask]

        if not df_afisat.empty:
            cols_show = ["Nume si Prenume", "CNP", "Vârsta", "Vaccin Necesar", "Status"]
            st.dataframe(
                df_afisat[cols_show].style.apply(highlight_rows, axis=1),
                use_container_width=True,
                height=600,
                hide_index=True
            )
        else:
            st.info("Niciun pacient nu corespunde filtrelor selectate.")


# ---- TAB 2: VACCINATION MANAGEMENT ----
with tab_record:
    st.subheader("💊 Gestiune Vaccinări")
    st.markdown("Selectează pacientul și bifează/debifează vaccinurile administrate.")

    children = get_children_patients()

    if not children:
        st.warning("Nu există pacienți copii în baza de date.")
    else:
        # Patient selector
        patient_options = {f"{p['nume']}  ·  CNP: {p['cnp']}": p for p in children}
        selected_name = st.selectbox("Pacient:", list(patient_options.keys()))
        selected_patient = patient_options[selected_name]

        dn = selected_patient['data_nasterii']
        st.markdown(f"**Vârstă:** {format_varsta(dn)}")

        if not dn:
            st.error("CNP invalid — nu se poate determina vârsta.")
        else:
            varsta_zile = (datetime.now() - dn).days

            # Get current vaccination records
            vaccinated_codes = get_vaccinated_codes_for_patient(selected_patient["id"])
            vaccines = get_all_vaccines()

            st.markdown("---")
            st.markdown("#### Calendarul de Vaccinare")
            st.caption("✅ = Vaccinat | ❌ = Nevaccinat · Bifează/debifează pentru a actualiza statusul.")

            changes_made = False

            for v in vaccines:
                is_due = varsta_zile >= v['target_age_days']
                is_vaccinated = v['cod'] in vaccinated_codes

                # Determine label with age info
                age_months = v['target_age_days'] / 30.44
                if age_months < 12:
                    age_label = f"{age_months:.0f} luni"
                else:
                    age_label = f"{age_months / 12:.0f} ani"

                if is_due:
                    label = f"{v['nume']}  ·  Programat: {age_label}"
                else:
                    days_until = v['target_age_days'] - varsta_zile
                    label = f"⏳ {v['nume']}  ·  Programat: {age_label} (peste {days_until} zile)"

                # Checkbox for each vaccine
                new_state = st.checkbox(
                    label,
                    value=is_vaccinated,
                    key=f"vax_{selected_patient['id']}_{v['cod']}",
                    disabled=not is_due  # Can't vaccinate for future vaccines
                )

                # Handle state changes
                if new_state != is_vaccinated:
                    changes_made = True
                    if new_state:
                        # Record vaccination
                        record_vaccination(
                            patient_id=selected_patient["id"],
                            vaccine_cod=v['cod'],
                            date_administered=datetime.now().date(),
                            notes="Înregistrat manual"
                        )
                    else:
                        # Delete vaccination record
                        history = get_vaccination_history(selected_patient["id"])
                        for h in history:
                            if h['vaccine_cod'] == v['cod']:
                                delete_vaccination_record(h['id'])
                                break

            if changes_made:
                st.cache_data.clear()
                st.rerun()


# ---- TAB 3: VACCINATION HISTORY ----
with tab_history:
    st.subheader("📋 Istoric Vaccinări")

    children = get_children_patients()

    if not children:
        st.warning("Nu există pacienți copii în baza de date.")
    else:
        # Patient selector — FULL CNP shown
        patient_options_hist = {f"{p['nume']}  ·  CNP: {p['cnp']}": p for p in children}
        selected_name_hist = st.selectbox(
            "Selectează pacientul:",
            list(patient_options_hist.keys()),
            key="hist_patient"
        )
        selected_patient_hist = patient_options_hist[selected_name_hist]

        st.markdown(f"**Vârstă:** {format_varsta(selected_patient_hist['data_nasterii'])}")

        # Current vaccination status
        st.markdown("#### Stare Curentă")
        dn = selected_patient_hist["data_nasterii"]
        all_statuses = get_all_vaccination_statuses(dn)
        vaccinated = get_vaccinated_codes_for_patient(selected_patient_hist["id"])

        if all_statuses:
            for status_text, vaccine_name, cod_cat in all_statuses:
                if "Adult" in status_text or "Eroare" in status_text:
                    continue
                if cod_cat in vaccinated:
                    st.markdown(f"- ✅ ~~{vaccine_name}~~ — **Administrat**")
                else:
                    st.markdown(f"- {status_text} {vaccine_name}")

        # Vaccination history table
        st.markdown("#### Istoricul Vaccinărilor")
        history = get_vaccination_history(selected_patient_hist["id"])

        if history:
            df_history = pd.DataFrame(history)
            df_history = df_history.rename(columns={
                "vaccine_name": "Vaccin",
                "date_administered": "Data Administrării",
                "lot_number": "Nr. Lot",
                "administered_by": "Administrat de",
                "notes": "Observații"
            })
            cols_hist = ["Vaccin", "Data Administrării", "Nr. Lot", "Administrat de", "Observații"]
            st.dataframe(df_history[cols_hist], use_container_width=True, hide_index=True)
        else:
            st.info("Nicio vaccinare înregistrată încă. Mergi la tab-ul 'Gestiune Vaccinări' pentru a bifa/debifa vaccinurile.")


# ---- TAB 4: EXPORT ----
with tab_export:
    st.subheader("📥 Export Catagrafie (Anexa 1)")

    luna_curenta = datetime.now().month
    an_curent = datetime.now().year
    LUNI_RO = {1: "Ianuarie", 2: "Februarie", 3: "Martie", 4: "Aprilie",
               5: "Mai", 6: "Iunie", 7: "Iulie", 8: "August",
               9: "Septembrie", 10: "Octombrie", 11: "Noiembrie", 12: "Decembrie"}
    st.markdown(f"Raport pentru copiii născuți în **{LUNI_RO[luna_curenta]} {an_curent}** · Paginare automată (13 rânduri/pagină).")

    df_export = build_operative_list()

    if df_export.empty:
        st.warning("Nu există date pentru export.")
    else:
        # Filter: keep only children born in the current month (CNP digits 4-5 = birth month)
        def cnp_born_in_current_month(cnp: str) -> bool:
            try:
                return int(str(cnp)[3:5]) == luna_curenta
            except (ValueError, IndexError):
                return False

        df_export = df_export[df_export['CNP'].apply(cnp_born_in_current_month)].copy()

        if df_export.empty:
            st.warning(f"Nu există copii născuți în luna {LUNI_RO[luna_curenta]} în baza de date.")
        else:
            df_preview = df_export[~df_export['Status'].isin(["🟢 La Zi"])]
            st.markdown(f"**Pacienți de exportat:** {len(df_preview)} (Urmează + Scadenți + Restanțieri)")
            st.markdown(f"**Pagini Excel:** {max(1, (len(df_preview) + 12) // 13)}")

            col_btn, col_info = st.columns([1, 2])
            with col_btn:
                excel_data = convert_df_to_catagrafie(df_export)
                st.download_button(
                    "📥 Descarcă Anexa 1 (Paginată)",
                    data=excel_data,
                    file_name=f'Catagrafie_Paginata_{LUNI_RO[luna_curenta]}_{an_curent}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    type="primary"
                )
            with col_info:
                st.info("💡 Exportul generează automat mai multe foi în Excel dacă ai mai mult de 13 copii.")
