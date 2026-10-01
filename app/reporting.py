"""Shared reporting model for the dashboard and monthly Excel export."""
import pandas as pd

from app.business_logic import (
    VACCINATION_SCHEDULE, as_datetime, format_varsta, get_all_vaccination_statuses,
    get_exact_due_date,
)
from app.database import get_children_patients, get_vaccinated_codes_by_patient

COLUMNS = ['ID', 'Nume si Prenume', 'CNP', 'Vârsta', 'Vârsta_datetime',
           'Vaccin Necesar', 'Status', '_cod_cat', '_all_codes', '_pending']


def build_operative_list(reference_date=None):
    ref = as_datetime(reference_date)
    vaccinated = get_vaccinated_codes_by_patient(ref)
    rows = []
    for patient in get_children_patients(ref):
        dob = patient['data_nasterii']
        pending = get_all_vaccination_statuses(dob, ref, vaccinated.get(patient['id'], set()))
        status = next((s for keyword in ('RESTANT', 'Scadent', 'Urmează')
                       for s, _, _ in pending if keyword in s), '🟢 La Zi')
        rows.append(dict(zip(COLUMNS, [patient['id'], patient['nume'], patient['cnp'],
            format_varsta(dob, ref), dob, ', '.join(v for _, v, _ in pending) or '-', status,
            pending[0][2] if pending else None, [c for _, _, c in pending], pending])))
    return pd.DataFrame(rows, columns=COLUMNS)


def filter_monthly_report(frame, reference_date=None):
    """Keep only doses due this month or overdue as of the selected day."""
    ref = as_datetime(reference_date)
    months_by_code = {code: months for months, (_, code) in VACCINATION_SCHEDULE.items()}
    rows = []
    for _, row in frame.iterrows():
        selected = []
        for status, name, code in row['_pending']:
            due = get_exact_due_date(row['Vârsta_datetime'], months_by_code[code])
            if 'RESTANT' in status or (due.year, due.month) == (ref.year, ref.month):
                selected.append((status, name, code))
        if selected:
            updated = row.to_dict()
            updated['_pending'] = selected
            updated['_all_codes'] = [c for _, _, c in selected]
            updated['Vaccin Necesar'] = ', '.join(n for _, n, _ in selected)
            rows.append(updated)
    return pd.DataFrame(rows, columns=frame.columns)
