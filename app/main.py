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
    get_db_stats
)
from app.excel_exporter import convert_df_to_catagrafie

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Vaccineasy V4.0",
    page_icon="💉",
    layout="wide"
)

# --- INITIALIZE DATABASE ---
init_db()


# =============================================================
# HELPER: Build the operative list from DB patients
# =============================================================
@st.cache_data(ttl=30)  # Cache for 30 seconds
def build_operative_list():
    """
    Build the operative patient list from the database.
    Returns a DataFrame with vaccination statuses computed live.
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
            # Up to date
            rows.append({
                "ID": patient["id"],
                "Nume si Prenume": patient["nume"],
                "CNP": patient["cnp"],
                "Vârsta": format_varsta(dn),
                "Vaccin Necesar": "-",
                "Status": "🟢 La Zi",
                "_cod_cat": None,
            })
            continue

        # Check for special statuses (Adult, Eroare)
        if any("Adult" in s[0] or "Eroare" in s[0] for s in all_statuses):
            continue

        # Filter out already-administered vaccines
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
            })
            continue

        # Add one row per pending vaccine
        for status_text, vaccin_name, cod_cat in pending:
            rows.append({
                "ID": patient["id"],
                "Nume si Prenume": patient["nume"],
                "CNP": patient["cnp"],
                "Vârsta": format_varsta(dn),
                "Vaccin Necesar": vaccin_name,
                "Status": status_text,
                "_cod_cat": cod_cat,
            })

    return pd.DataFrame(rows)


# =============================================================
# STYLING
# =============================================================
def highlight_rows(row):
    """Color-code rows by vaccination status."""
    status = row['Status']
    if "RESTANT" in status:
        color = '#ff4b4b'
    elif "Scadent" in status:
        color = '#ffa421'
    elif "Urmează" in status:
        color = '#21c354'
    else:
        color = 'transparent'
    return [
        f'background-color: {color}; color: white; font-weight: bold' if col == 'Status' else ''
        for col in row.index
    ]


# =============================================================
# SIDEBAR
# =============================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/syringe.png", width=60)
    st.title("Vaccineasy")
    st.caption("v4.0 — cu bază de date")

    st.markdown("---")

    # Database stats
    stats = get_db_stats()
    st.metric("Pacienți în DB", stats["total_patients"])
    st.metric("Vaccinări Înregistrate", stats["total_vaccination_records"])

    st.markdown("---")

    # Excel Import Section
    st.header("📁 Import Date")
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
    st.info("ℹ️ Datele sunt salvate local. Nu se pierd la repornire.")


# =============================================================
# MAIN CONTENT — TABS
# =============================================================
st.title("💉 Vaccineasy — Sistem Management Vaccinări")

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
        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Copii Înregistrați", df["ID"].nunique())

        restant_count = len(df[df["Status"].str.contains("RESTANT", na=False)])
        scadent_count = len(df[df["Status"].str.contains("Scadent", na=False)])
        la_zi_count = len(df[df["Status"].str.contains("La Zi", na=False)])

        c2.metric("🔴 Restanțieri", restant_count)
        c3.metric("🟡 De Vaccinat", scadent_count)
        c4.metric("🟢 La Zi", la_zi_count)

        st.markdown("---")

        # Filters
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


# ---- TAB 2: RECORD VACCINATION ----
with tab_record:
    st.subheader("💊 Înregistrare Vaccinare")
    st.markdown("Selectează pacientul și vaccinul administrat.")

    children = get_children_patients()

    if not children:
        st.warning("Nu există pacienți copii în baza de date.")
    else:
        # Patient selector
        patient_options = {f"{p['nume']} (CNP: ...{p['cnp'][-4:]})": p for p in children}
        selected_name = st.selectbox("Pacient:", list(patient_options.keys()))
        selected_patient = patient_options[selected_name]

        st.markdown(f"**Vârstă:** {format_varsta(selected_patient['data_nasterii'])}")

        # Show what's already been administered
        vaccinated_codes = get_vaccinated_codes_for_patient(selected_patient["id"])
        if vaccinated_codes:
            st.success(f"Vaccinuri deja administrate: {', '.join(vaccinated_codes)}")

        st.markdown("---")

        # Vaccine selector
        vaccines = get_all_vaccines()
        vaccine_options = {f"{v['nume']} ({v['cod']})": v for v in vaccines}
        selected_vaccine_name = st.selectbox("Vaccin administrat:", list(vaccine_options.keys()))
        selected_vaccine = vaccine_options[selected_vaccine_name]

        # Already administered warning
        if selected_vaccine['cod'] in vaccinated_codes:
            st.warning("⚠️ Acest vaccin a fost deja înregistrat. Salvarea va actualiza înregistrarea.")

        # Input fields
        col1, col2 = st.columns(2)
        with col1:
            date_admin = st.date_input("Data administrării:", value=datetime.now().date())
        with col2:
            lot_number = st.text_input("Număr lot:", placeholder="ex: AB1234")

        administered_by = st.text_input("Administrat de:", placeholder="Dr. Popescu")
        notes = st.text_area("Observații:", placeholder="Opțional", height=80)

        if st.button("💾 Salvează Vaccinarea", type="primary", use_container_width=True):
            result = record_vaccination(
                patient_id=selected_patient["id"],
                vaccine_cod=selected_vaccine["cod"],
                date_administered=date_admin,
                lot_number=lot_number if lot_number else None,
                administered_by=administered_by if administered_by else None,
                notes=notes if notes else None,
            )

            if result["success"]:
                st.success(result["message"])
                st.cache_data.clear()
                st.balloons()
            else:
                st.error(result["message"])


# ---- TAB 3: VACCINATION HISTORY ----
with tab_history:
    st.subheader("📋 Istoric Vaccinări")

    children = get_children_patients()

    if not children:
        st.warning("Nu există pacienți copii în baza de date.")
    else:
        patient_options_hist = {f"{p['nume']} (CNP: ...{p['cnp'][-4:]})": p for p in children}
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
            st.info("Nicio vaccinare înregistrată încă pentru acest pacient.")


# ---- TAB 4: EXPORT ----
with tab_export:
    st.subheader("📥 Export Catagrafie (Anexa 1)")
    st.markdown("Generează raportul oficial cu paginare automată (13 rânduri/pagină).")

    df_export = build_operative_list()

    if df_export.empty:
        st.warning("Nu există date pentru export.")
    else:
        # Show preview
        df_preview = df_export[~df_export['Status'].isin(["🟢 La Zi", "🟢 Urmează"])]
        st.markdown(f"**Pacienți de exportat:** {len(df_preview)} (Scadenți + Restanțieri)")
        st.markdown(f"**Pagini Excel:** {max(1, (len(df_preview) + 12) // 13)}")

        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            excel_data = convert_df_to_catagrafie(df_export)
            st.download_button(
                "📥 Descarcă Anexa 1 (Paginată)",
                data=excel_data,
                file_name=f'Catagrafie_Paginata_{datetime.now().strftime("%B_%Y")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                type="primary"
            )
        with col_info:
            st.info("💡 Exportul generează automat mai multe foi în Excel dacă ai mai mult de 13 copii.")
