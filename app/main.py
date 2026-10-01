"""Vaccineasy clinical workspace. All translations are presentation-only."""
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from app.business_logic import VACCINATION_SCHEDULE, as_datetime, get_all_vaccination_statuses, get_exact_due_date
from app.database import (
    init_db, import_patients_from_excel, get_children_patients, get_db_stats,
    get_vaccinated_codes_for_patient, get_vaccination_history, save_vaccination_selection,
)
from app.excel_exporter import convert_df_to_catagrafie
from app.reporting import build_operative_list, filter_monthly_report
from app.presentation import (
    STATUS_LABELS, VACCINE_LABELS, MONTHS, display_date, display_note, display_error,
    display_patient_frame, patient_context_html,
)

st.set_page_config(page_title='Vaccineasy · Practice workspace', page_icon='💉',
                   layout='wide', initial_sidebar_state='expanded')
style_path = Path(__file__).with_name('styles.css')
if style_path.exists():
    st.markdown(f'<style>{style_path.read_text(encoding="utf-8")}</style>', unsafe_allow_html=True)


def highlight_rows(row):
    colors = {'Overdue': ('#fff0ef', '#862b26'), 'Due': ('#fff5dc', '#785200'),
              'Upcoming': ('#eaf4ff', '#205584'), 'Up to date': ('#e8f5ed', '#246342')}
    bg, fg = colors.get(row['Status'], ('#ffffff', '#18334b'))
    return [f'background-color:{bg};color:{fg}' for _ in row]


try:
    init_db()
except Exception:
    st.error('The local database could not be opened. Check access to the data folder and restart the app.')
    st.stop()

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-mark">+</span> Vaccineasy</div>', unsafe_allow_html=True)
    st.caption('FAMILY PRACTICE · VACCINATION REGISTER')
    stats_area = st.container()
    st.divider()
    st.subheader('Reference date')
    selected_date = st.date_input('View records as of', value=date.today(),
        min_value=date(1900, 1, 1), max_value=date.today(), format='DD.MM.YYYY',
        help='Controls ages, status, patient history and the monthly report. Recording always uses today.')
    reference_date = as_datetime(selected_date)
    if selected_date < date.today():
        st.warning(f'Historical view · {display_date(selected_date)}')
    st.divider()
    st.subheader('Import patients')
    upload = st.file_uploader('ICMED patient file', type=['xlsx', 'xls', 'csv'],
        help='Keep the ICMED column names: Nume (surname), Prenume (given name), CNP. Telefon is optional.')
    st.caption('Required columns: Nume, Prenume, CNP. Existing patients are matched by CNP.')
    st.caption('On first import, doses due before this month are assumed completed. '
               'They are labelled unconfirmed in patient history.')
    if st.button('Import patients', type='primary', disabled=upload is None, use_container_width=True):
        with st.spinner('Importing the patient file…'):
            result = import_patients_from_excel(upload)
        summary = f"Added {result['imported']} · Updated {result['updated']} · Skipped {result['skipped']}"
        if result['errors']:
            st.warning(summary)
        else:
            st.success(f'Import complete. {summary}')
        for error in result['errors']:
            st.warning(display_error(error))
    with stats_area:
        stats = get_db_stats()
        st.metric('Registered patients', stats['total_patients'])
        st.metric('Vaccination records', stats['total_vaccination_records'])
        st.caption('Record count includes assumed doses.')
    st.divider()
    st.caption('LOCAL STORAGE\n\nPatient records are stored on the computer running this app. '
               'Docker installations need the configured persistent data volume.')

heading, context = st.columns([3, 2])
with heading:
    st.markdown('<div class="eyebrow">Practice workspace</div>', unsafe_allow_html=True)
    st.title('Vaccination care')
    st.caption('Review what is due. Record care. Prepare the monthly register.')
with context:
    st.markdown(f'<div class="date-context"><span>Viewing status as of</span>'
                f'<strong>{display_date(selected_date)}</strong></div>', unsafe_allow_html=True)
if 'saved_message' in st.session_state:
    st.success(st.session_state.pop('saved_message'))

dashboard, record_tab, history_tab, export_tab = st.tabs([
    'Overview', 'Record vaccination', 'Patient history', 'Monthly report'])
frame = build_operative_list(reference_date)

with dashboard:
    st.subheader('Your patient list')
    st.caption('Children within the existing pediatric age limit on the reference date. '
               'The most urgent pending dose determines each patient’s status.')
    cards = st.columns(4)
    cards[0].metric('Children', len(frame))
    cards[1].metric('Overdue', int(frame['Status'].eq('🔴 RESTANT').sum()))
    cards[2].metric('Due', int(frame['Status'].eq('🟡 Scadent').sum()))
    cards[3].metric('Up to date', int(frame['Status'].eq('🟢 La Zi').sum()))
    st.caption(f"Children upcoming within 31 days: {int(frame['Status'].eq('🟢 Urmează').sum())}. "
               'Due: 0–30 days after the scheduled date. Overdue: more than 30 days after.')
    filters = st.multiselect('Show patients with status',
        ['🔴 RESTANT', '🟡 Scadent', '🟢 Urmează', '🟢 La Zi'],
        default=['🔴 RESTANT', '🟡 Scadent'], format_func=STATUS_LABELS.get)
    visible = frame[frame['Status'].isin(filters)]
    if frame.empty:
        st.info('No eligible children on this date. Import an ICMED patient file in the sidebar, '
                'or review the reference date if you have already imported patients.')
    elif visible.empty:
        st.info('No patients match these status filters. Choose Upcoming or Up to date to see other patients.')
    else:
        st.caption(f'{len(visible)} of {len(frame)} children shown · All pending doses are listed for each child.')
        st.dataframe(display_patient_frame(visible).style.apply(highlight_rows, axis=1),
                     use_container_width=True, hide_index=True,
                     column_config={'CNP': st.column_config.TextColumn('CNP', help='Romanian personal identification number')})

with record_tab:
    st.subheader('Record vaccination')
    st.caption(f'Newly checked doses are recorded today: {display_date(date.today())}. '
               'The reference date does not change the administration date.')
    children = get_children_patients()
    if not children:
        st.info('No eligible children today. Import a patient file to start recording vaccinations.')
    else:
        patients = {p['id']: p for p in children}
        patient_id = st.selectbox('Find a patient by name or CNP', list(patients),
            format_func=lambda key: f"{patients[key]['nume']} · CNP {patients[key]['cnp']}", key='record_patient')
        patient = patients[patient_id]
        dob = patient['data_nasterii']
        st.markdown(patient_context_html(patient), unsafe_allow_html=True)
        vaccinated = get_vaccinated_codes_for_patient(patient_id)
        assumed = {r['vaccine_cod'] for r in get_vaccination_history(patient_id) if r['assumed']}
        with st.form(f'vaccines_{patient_id}'):
            doses_col, details_col = st.columns([3, 2], gap='large')
            selection = set()
            with doses_col:
                st.markdown('#### Scheduled doses')
                st.caption('Checked doses already have a record. Future doses are disabled.')
                for months, (_, code) in VACCINATION_SCHEDULE.items():
                    due = get_exact_due_date(dob, months)
                    days_until = (due - as_datetime()).days
                    label = VACCINE_LABELS[code]
                    if days_until > 0:
                        label += f' — in {days_until} days'
                    if code in assumed:
                        label += ' — assumed at import, unconfirmed'
                    if st.checkbox(label, value=code in vaccinated, disabled=days_until > 0,
                                   key=f'vaccine_{patient_id}_{code}',
                                   help=f'Scheduled date: {display_date(due)}'):
                        selection.add(code)
            with details_col:
                st.markdown('#### Administration details')
                st.caption('Applies only to newly checked doses. Existing dates and details are kept.')
                lot = st.text_input('Batch / lot number (optional)')
                administered_by = st.text_input('Administered by (optional)')
                st.warning('Unchecking a recorded dose deletes its record when you save. '
                           'Check the patient name and CNP before saving.')
                st.caption('Assumed doses are not confirmed administrations. Leaving them checked keeps their existing record.')
            submitted = st.form_submit_button('Save vaccination changes', type='primary')
        if submitted:
            try:
                save_vaccination_selection(patient_id, selection, lot, administered_by)
            except ValueError as exc:
                st.error(display_error(str(exc)))
            except Exception:
                st.error('No changes were saved. Check access to the local database and try again.')
            else:
                st.session_state['saved_message'] = 'Vaccination changes saved. The patient list and history are up to date.'
                st.rerun()

with history_tab:
    st.subheader('Patient history')
    st.caption(f'Schedule status on {display_date(selected_date)}. The full record history is shown below.')
    children = get_children_patients(reference_date)
    if not children:
        st.info('No eligible children on the reference date. Review the date or import a patient file.')
    else:
        history_patients = {p['id']: p for p in children}
        history_id = st.selectbox('Find a patient by name or CNP', list(history_patients), key='history_patient',
            format_func=lambda key: f"{history_patients[key]['nume']} · CNP {history_patients[key]['cnp']}")
        patient = history_patients[history_id]
        dob = patient['data_nasterii']
        st.markdown(patient_context_html(patient, reference_date), unsafe_allow_html=True)
        history = get_vaccination_history(history_id)
        done = {r['vaccine_cod']: r for r in history if r['date_administered'] <= selected_date}
        pending = {code: status for status, _, code in get_all_vaccination_statuses(dob, reference_date)}
        for _, (_, code) in VACCINATION_SCHEDULE.items():
            name = VACCINE_LABELS[code]
            if code in done:
                if done[code]['assumed']:
                    st.markdown(f'- ◻ {name} — **Assumed at import · not clinically confirmed**')
                else:
                    st.markdown(f'- ✓ ~~{name}~~ — **Administered**')
            else:
                st.markdown(f"- {name} — **{STATUS_LABELS.get(pending.get(code), 'Scheduled later')}**")
        st.markdown('#### Full record history')
        st.caption('Includes records after the reference date. Dates on assumed records are scheduled dates, '
                   'not confirmed administration dates.')
        if history:
            table = pd.DataFrame(history)
            table['Record type'] = table['assumed'].map({True: 'Assumed at import', False: 'Confirmed'})
            table['vaccine_name'] = table['vaccine_cod'].map(VACCINE_LABELS)
            table['notes'] = table['notes'].map(display_note)
            table = table.rename(columns={'vaccine_name': 'Vaccine', 'date_administered': 'Recorded date',
                'lot_number': 'Batch / lot', 'administered_by': 'Administered by', 'notes': 'Notes'})
            st.dataframe(table[['Vaccine', 'Recorded date', 'Record type', 'Batch / lot', 'Administered by', 'Notes']],
                         use_container_width=True, hide_index=True)
        else:
            st.info('No vaccination records yet. Use Record vaccination to record an administered dose.')

with export_tab:
    st.subheader('Monthly vaccination report')
    month = MONTHS[reference_date.month - 1]
    st.write(f'Anexa 1 · {month} {reference_date.year}')
    st.caption('Includes unrecorded doses scheduled this month and doses overdue on the reference date. '
               'The Romanian workbook format is preserved. Pneumococcal columns mirror hexavalent doses.')
    report = filter_monthly_report(frame, reference_date)
    pages = (len(report) + 12) // 13
    st.markdown(f'**{len(report)} {"patient" if len(report) == 1 else "patients"}** · '
                f'**{pages} Excel {"page" if pages == 1 else "pages"}** · 13 patients per page')
    if report.empty:
        st.info('No patients need this report for the selected date. Choose another reference date to review a different month.')
    else:
        st.dataframe(display_patient_frame(report, include_status=False), use_container_width=True, hide_index=True)
        st.download_button('Download Anexa 1 (.xlsx)',
            data=convert_df_to_catagrafie(report, reference_date),
            file_name=f'Catagrafie_{reference_date:%Y_%m}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', type='primary')
