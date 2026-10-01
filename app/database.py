"""Transactional SQLite storage. Historical assumptions are explicitly labelled."""
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, Patient, Vaccine, VaccinationRecord, ImportBaseline
from app.business_logic import (
    VACCINATION_SCHEDULE, as_datetime, decode_cnp, get_exact_due_date, is_child,
)

DB_DIR = os.environ.get('VACCINEASY_DB_DIR', str(Path(__file__).resolve().parent.parent / 'data'))
DB_PATH = str(Path(DB_DIR) / 'vaccineasy.db')
DATABASE_URL = f'sqlite:///{DB_PATH}'
_engine = None
_SessionLocal = None
ASSUMED_NOTE = 'Auto-înregistrat la import — presupus, neconfirmat clinic'


def get_engine():
    global _engine
    if _engine is None:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(DATABASE_URL, connect_args={'timeout': 30})

        @event.listens_for(_engine, 'connect')
        def configure_sqlite(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA journal_mode=WAL')
    return _engine


def get_session() -> Session:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal()


def init_db():
    Base.metadata.create_all(get_engine())
    with get_session() as session, session.begin():
        for months, (name, code) in VACCINATION_SCHEDULE.items():
            vaccine = session.scalar(select(Vaccine).where(Vaccine.cod == code))
            if vaccine is None:
                vaccine = Vaccine(cod=code)
                session.add(vaccine)
            vaccine.nume = name
            # Compatibility field only. Due dates always use calendar months.
            vaccine.target_age_days = round(months * 365.25 / 12)
            vaccine.description = f'Programat la {months} luni; calcul calendaristic.'
        session.flush()
        uninitialized = select(Patient).outerjoin(ImportBaseline).where(ImportBaseline.patient_id.is_(None))
        for patient in session.scalars(uninitialized):
            if patient.data_nasterii:
                _auto_vaccinate_patient(session, patient.id, patient.data_nasterii,
                                       patient.created_at or datetime.now())


def _auto_vaccinate_patient(session, patient_id, dob, reference_date=None):
    """Complete pre-import months once; never silently close later missed doses.

    An assumed record uses the scheduled date, not a fabricated administration
    today. Notes identify that this date and administration are unconfirmed.
    """
    if session.get(ImportBaseline, patient_id):
        return
    ref = as_datetime(reference_date)
    for months, (_, code) in VACCINATION_SCHEDULE.items():
        due = get_exact_due_date(dob, months)
        if due >= ref.replace(day=1):
            continue
        vaccine = session.scalar(select(Vaccine).where(Vaccine.cod == code))
        if vaccine is None:
            continue
        existing = session.scalar(select(VaccinationRecord).where(
            VaccinationRecord.patient_id == patient_id,
            VaccinationRecord.vaccine_id == vaccine.id))
        if existing is None:
            session.add(VaccinationRecord(patient_id=patient_id, vaccine_id=vaccine.id,
                                          date_administered=due.date(), notes=ASSUMED_NOTE))
    session.add(ImportBaseline(patient_id=patient_id, cutoff_date=ref.date()))
    session.flush()


def import_patients_from_excel(uploaded_file):
    result = dict(imported=0, updated=0, skipped=0, errors=[])
    try:
        uploaded_file.seek(0)
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix == '.csv':
            try:
                frame = pd.read_csv(uploaded_file, sep=None, engine='python', dtype=str,
                                    keep_default_na=False, encoding='utf-8-sig')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                frame = pd.read_csv(uploaded_file, sep=None, engine='python', dtype=str,
                                    keep_default_na=False, encoding='cp1250')
        elif suffix in ('.xlsx', '.xls'):
            frame = pd.read_excel(uploaded_file, dtype=str, keep_default_na=False,
                                  engine='xlrd' if suffix == '.xls' else 'openpyxl')
        else:
            raise ValueError('Format acceptat: XLSX, XLS sau CSV.')
        frame.columns = [str(c).strip().lower() for c in frame.columns]
        if not frame.columns.is_unique:
            raise ValueError('Fișierul conține coloane duplicate.')
        if not {'nume', 'prenume', 'cnp'}.issubset(frame.columns):
            raise ValueError('Sunt necesare coloanele Nume, Prenume, CNP.')
    except Exception as exc:
        result['errors'].append(f'Fișierul nu poate fi citit: {exc}')
        return result

    try:
        with get_session() as session, session.begin():
            for index, row in frame.iterrows():
                # Numeric Excel identifiers sometimes arrive with a trailing .0.
                raw = re.sub(r'\.0+$', '', str(row['cnp']).strip())
                cnp = ''.join(c for c in raw if c.isascii() and c.isdigit())
                dob = decode_cnp(cnp)
                name = ' '.join(str(row[c]).strip() for c in ('nume', 'prenume')).strip()
                if dob is None or dob > as_datetime() or not name:
                    result['skipped'] += 1
                    result['errors'].append(f'Rândul {index + 2}: CNP, dată de naștere sau nume invalid.')
                    continue
                patient = session.scalar(select(Patient).where(Patient.cnp == cnp))
                if patient is None:
                    patient = Patient(cnp=cnp, nume=name, data_nasterii=dob.date())
                    session.add(patient)
                    session.flush()
                    result['imported'] += 1
                else:
                    patient.nume = name
                    patient.data_nasterii = dob.date()
                    patient.updated_at = datetime.now()
                    result['updated'] += 1
                if 'telefon' in frame.columns and str(row['telefon']).strip():
                    patient.telefon = str(row['telefon']).strip()
                _auto_vaccinate_patient(session, patient.id, dob)
    except Exception:
        result['imported'] = result['updated'] = 0
        result['errors'].append('Importul a fost anulat integral din cauza unei erori de salvare.')
    return result


def get_all_patients():
    with get_session() as session:
        return [dict(id=p.id, cnp=p.cnp, nume=p.nume, telefon=p.telefon,
                     data_nasterii=as_datetime(p.data_nasterii) if p.data_nasterii else None,
                     created_at=p.created_at, updated_at=p.updated_at)
                for p in session.scalars(select(Patient).order_by(Patient.nume, Patient.id))]


def get_children_patients(reference_date=None):
    return [p for p in get_all_patients() if is_child(p['data_nasterii'], reference_date)]


def delete_patient(patient_id):
    with get_session() as session, session.begin():
        patient = session.get(Patient, patient_id)
        if patient is None:
            return False
        session.delete(patient)
        return True


def get_vaccinated_codes_by_patient(reference_date=None):
    ref = as_datetime(reference_date).date()
    result = {}
    with get_session() as session:
        rows = session.execute(select(VaccinationRecord.patient_id, Vaccine.cod)
                               .join(Vaccine).where(VaccinationRecord.date_administered <= ref))
        for patient_id, code in rows:
            result.setdefault(patient_id, set()).add(code)
    return result


def get_vaccinated_codes_for_patient(patient_id, reference_date=None):
    with get_session() as session:
        return set(session.scalars(select(Vaccine.cod).join(VaccinationRecord).where(
            VaccinationRecord.patient_id == patient_id,
            VaccinationRecord.date_administered <= as_datetime(reference_date).date())))


def get_vaccination_history(patient_id):
    with get_session() as session:
        rows = session.execute(select(VaccinationRecord, Vaccine).join(Vaccine).where(
            VaccinationRecord.patient_id == patient_id).order_by(VaccinationRecord.date_administered))
        return [dict(id=r.id, vaccine_cod=v.cod, vaccine_name=v.nume,
                     date_administered=r.date_administered, lot_number=r.lot_number,
                     administered_by=r.administered_by, notes=r.notes, created_at=r.created_at,
                     assumed=(r.notes or '').startswith('Auto-înregistrat')) for r, v in rows]


def get_all_vaccines():
    with get_session() as session:
        return [dict(id=v.id, cod=v.cod, nume=v.nume, target_age_days=v.target_age_days)
                for v in session.scalars(select(Vaccine).order_by(Vaccine.target_age_days))]


def record_vaccination(patient_id, vaccine_cod, date_administered,
                       lot_number=None, administered_by=None, notes=None):
    try:
        with get_session() as session, session.begin():
            patient = session.get(Patient, patient_id)
            vaccine = session.scalar(select(Vaccine).where(Vaccine.cod == vaccine_cod))
            if patient is None or vaccine is None:
                raise ValueError('Pacientul sau vaccinul nu există.')
            day = as_datetime(date_administered).date()
            if day > as_datetime().date() or (patient.data_nasterii and day < patient.data_nasterii):
                raise ValueError('Data administrării este invalidă.')
            record = session.scalar(select(VaccinationRecord).where(
                VaccinationRecord.patient_id == patient_id, VaccinationRecord.vaccine_id == vaccine.id))
            if record is None:
                record = VaccinationRecord(patient_id=patient_id, vaccine_id=vaccine.id)
                session.add(record)
            record.date_administered = day
            record.lot_number = lot_number
            record.administered_by = administered_by
            record.notes = notes
        return dict(success=True, message='Vaccinarea a fost salvată.')
    except ValueError as exc:
        return dict(success=False, message=str(exc))


def delete_vaccination_record(record_id):
    with get_session() as session, session.begin():
        record = session.get(VaccinationRecord, record_id)
        if record is None:
            return False
        session.delete(record)
        return True


def save_vaccination_selection(patient_id, selected_codes, lot_number='', administered_by=''):
    """Save the entire form atomically. Preserve dates of unchanged records."""
    today = as_datetime()
    with get_session() as session, session.begin():
        patient = session.get(Patient, patient_id)
        if patient is None or not is_child(patient.data_nasterii, today):
            raise ValueError('Pacientul nu este eligibil pentru acest formular.')
        vaccines = {v.cod: v for v in session.scalars(select(Vaccine))}
        records = {r.vaccine_id: r for r in session.scalars(select(VaccinationRecord).where(
            VaccinationRecord.patient_id == patient_id))}
        if not set(selected_codes).issubset(c for _, c in VACCINATION_SCHEDULE.values()):
            raise ValueError('Cod de vaccin necunoscut.')
        for months, (_, code) in VACCINATION_SCHEDULE.items():
            vaccine = vaccines[code]
            record = records.get(vaccine.id)
            if get_exact_due_date(patient.data_nasterii, months) > today:
                if code in selected_codes and record is None:
                    raise ValueError('Vaccinul nu este încă scadent.')
                continue
            if code in selected_codes and record is None:
                session.add(VaccinationRecord(patient_id=patient_id, vaccine_id=vaccine.id,
                    date_administered=today.date(), lot_number=lot_number or None,
                    administered_by=administered_by or None, notes='Înregistrat manual'))
            elif code not in selected_codes and record is not None:
                session.delete(record)


def get_db_stats():
    with get_session() as session:
        return dict(total_patients=session.query(Patient).count(),
                    total_vaccination_records=session.query(VaccinationRecord).count())
