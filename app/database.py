"""
Vaccineasy v4.0 — Database Access Layer
SQLite database initialization, patient import, vaccination recording.
"""

import os
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models import Base, Patient, Vaccine, VaccinationRecord
from app.business_logic import decode_cnp, VACCINATION_SCHEDULE

# Database path — default to ./data/vaccineasy.db
DB_DIR = os.environ.get("VACCINEASY_DB_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))
DB_PATH = os.path.join(DB_DIR, "vaccineasy.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _engine = create_engine(DATABASE_URL, echo=False)
    return _engine


def get_session() -> Session:
    """Get a new database session."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def init_db():
    """Create all tables and seed the vaccine reference data."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    _seed_vaccines()


def _seed_vaccines():
    """Populate the vaccines table with Romania's national schedule if empty."""
    session = get_session()
    try:
        existing = session.query(Vaccine).count()
        if existing > 0:
            return  # Already seeded

        for target_days, (name, code) in VACCINATION_SCHEDULE.items():
            vaccine = Vaccine(
                cod=code,
                nume=name,
                target_age_days=target_days,
                description=f"Vaccin programat la {target_days} zile de viață"
            )
            session.add(vaccine)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# =============================================================
# PATIENT OPERATIONS
# =============================================================

def import_patients_from_excel(uploaded_file) -> dict:
    """
    Import patients from an Excel/CSV file into the database.
    Upserts by CNP — existing patients are updated, new ones are inserted.

    Returns: {"imported": int, "updated": int, "skipped": int, "errors": list}
    """
    try:
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file)
                if len(df.columns) < 2:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, sep=';')
            except Exception:
                return {"imported": 0, "updated": 0, "skipped": 0,
                        "errors": ["Nu am putut citi formatul CSV."]}
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        return {"imported": 0, "updated": 0, "skipped": 0,
                "errors": [f"Eroare la citirea fișierului: {e}"]}

    # Normalize column names
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    # Identify Nume, Prenume, CNP
    col_nume = next((c for c in df.columns if c == 'nume'), None)
    col_prenume = next((c for c in df.columns if c == 'prenume'), None)
    col_cnp = next((c for c in df.columns if 'cnp' in c), None)

    if not col_cnp:
        return {"imported": 0, "updated": 0, "skipped": 0,
                "errors": [f"Lipsește coloana 'CNP'. Coloane găsite: {list(df.columns)}"]}
    
    if not col_nume and not col_prenume:
        return {"imported": 0, "updated": 0, "skipped": 0,
                "errors": [f"Lipsește 'Nume' sau 'Prenume'. Coloane găsite: {list(df.columns)}"]}

    session = get_session()
    imported = 0
    updated = 0
    skipped = 0
    errors = []

    try:
        for _, row in df.iterrows():
            cnp = str(row[col_cnp]).strip()
            cnp = ''.join(filter(str.isdigit, cnp))
            
            # Retrieve Nume and Prenume
            nume_part = str(row[col_nume]).strip() if col_nume and pd.notna(row.get(col_nume)) else ""
            prenume_part = str(row[col_prenume]).strip() if col_prenume and pd.notna(row.get(col_prenume)) else ""
            
            # Concatenate Nume + Prenume, falling back gracefully
            nume_full = " ".join(filter(None, [nume_part, prenume_part]))
            
            if not nume_full:
                nume_full = "Necunoscut"

            if len(cnp) < 13:
                skipped += 1
                continue

            cnp = cnp[:13]
            data_nasterii = decode_cnp(cnp)

            # Check if patient already exists
            existing = session.query(Patient).filter_by(cnp=cnp).first()

            if existing:
                # Update
                existing.nume = nume_full
                if data_nasterii:
                    existing.data_nasterii = data_nasterii.date()
                existing.updated_at = datetime.now()
                updated += 1
            else:
                # Insert
                patient = Patient(
                    cnp=cnp,
                    nume=nume_full,
                    telefon=None,
                    data_nasterii=data_nasterii.date() if data_nasterii else None
                )
                session.add(patient)
                session.flush()  # Get the patient ID before commit

                # Auto-vaccinate: assume all age-appropriate vaccines are done
                if data_nasterii:
                    _auto_vaccinate_patient(session, patient.id, data_nasterii)

                imported += 1

        session.commit()

    except Exception as e:
        session.rollback()
        errors.append(f"Eroare la import: {e}")
    finally:
        session.close()

    return {"imported": imported, "updated": updated, "skipped": skipped, "errors": errors}


def get_all_patients() -> list:
    """Retrieve all patients from the database."""
    session = get_session()
    try:
        patients = session.query(Patient).order_by(Patient.nume).all()
        # Detach from session
        result = []
        for p in patients:
            result.append({
                "id": p.id,
                "cnp": p.cnp,
                "nume": p.nume,
                "telefon": p.telefon,
                "data_nasterii": datetime.combine(p.data_nasterii, datetime.min.time()) if p.data_nasterii else None,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            })
        return result
    finally:
        session.close()


def get_children_patients() -> list:
    """Retrieve only patients under 15 years old."""
    all_patients = get_all_patients()
    children = []
    for p in all_patients:
        if p["data_nasterii"]:
            age_days = (datetime.now() - p["data_nasterii"]).days
            if age_days / 365.25 <= 15:
                children.append(p)
    return children


def delete_patient(patient_id: int) -> bool:
    """Delete a patient by ID."""
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if patient:
            session.delete(patient)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


from datetime import datetime, timedelta

from app.business_logic import VACCINATION_SCHEDULE, get_exact_due_date

def _auto_vaccinate_patient(session: Session, patient_id: int, data_nasterii: datetime):
    """
    Auto-create vaccination records for all vaccines the child's age has surpassed.
    SKIPS vaccines that are due in the CURRENT month, so they can be reported
    in the Anexa 1 'Lot de bază' for this month.
    """
    current_year = datetime.now().year
    current_month = datetime.now().month

    for target_months, (_, cod) in VACCINATION_SCHEDULE.items():
        due_date = get_exact_due_date(data_nasterii, target_months)
        
        if datetime.now() >= due_date:
            # If due THIS month, do NOT auto-vaccinate. Leave it for 'Lot de bază'.
            if due_date.year == current_year and due_date.month == current_month:
                continue

            vaccine = session.query(Vaccine).filter_by(cod=cod).first()
            if not vaccine:
                continue

            # Skip if already recorded
            existing = session.query(VaccinationRecord).filter_by(
                patient_id=patient_id, vaccine_id=vaccine.id
            ).first()
            if existing:
                continue

            record = VaccinationRecord(
                patient_id=patient_id,
                vaccine_id=vaccine.id,
                date_administered=datetime.now().date(),
                notes="Auto-înregistrat la import"
            )
            session.add(record)


def delete_vaccination_record(record_id: int) -> bool:
    """Delete a vaccination record by ID (marks vaccine as not administered)."""
    session = get_session()
    try:
        record = session.query(VaccinationRecord).filter_by(id=record_id).first()
        if record:
            session.delete(record)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


# =============================================================
# VACCINATION RECORD OPERATIONS
# =============================================================

def record_vaccination(patient_id: int, vaccine_cod: str,
                       date_administered: datetime,
                       lot_number: Optional[str] = None,
                       administered_by: Optional[str] = None,
                       notes: Optional[str] = None) -> dict:
    """
    Record a vaccination for a patient.
    Returns: {"success": bool, "message": str}
    """
    session = get_session()
    try:
        patient = session.query(Patient).filter_by(id=patient_id).first()
        if not patient:
            return {"success": False, "message": "Pacientul nu a fost găsit."}

        vaccine = session.query(Vaccine).filter_by(cod=vaccine_cod).first()
        if not vaccine:
            return {"success": False, "message": f"Vaccinul '{vaccine_cod}' nu a fost găsit."}

        # Check for existing record
        existing = session.query(VaccinationRecord).filter_by(
            patient_id=patient_id, vaccine_id=vaccine.id
        ).first()

        if existing:
            # Update existing record
            existing.date_administered = date_administered
            existing.lot_number = lot_number
            existing.administered_by = administered_by
            existing.notes = notes
            session.commit()
            return {"success": True, "message": "Înregistrarea de vaccinare a fost actualizată."}

        record = VaccinationRecord(
            patient_id=patient_id,
            vaccine_id=vaccine.id,
            date_administered=date_administered,
            lot_number=lot_number,
            administered_by=administered_by,
            notes=notes
        )
        session.add(record)
        session.commit()
        return {"success": True, "message": "Vaccinarea a fost înregistrată cu succes!"}

    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Eroare: {e}"}
    finally:
        session.close()


def get_vaccination_history(patient_id: int) -> list:
    """Get all vaccination records for a patient."""
    session = get_session()
    try:
        records = (
            session.query(VaccinationRecord)
            .filter_by(patient_id=patient_id)
            .order_by(VaccinationRecord.date_administered)
            .all()
        )
        result = []
        for r in records:
            vaccine = session.query(Vaccine).filter_by(id=r.vaccine_id).first()
            result.append({
                "id": r.id,
                "vaccine_cod": vaccine.cod if vaccine else "?",
                "vaccine_name": vaccine.nume if vaccine else "?",
                "date_administered": r.date_administered,
                "lot_number": r.lot_number,
                "administered_by": r.administered_by,
                "notes": r.notes,
                "created_at": r.created_at,
            })
        return result
    finally:
        session.close()


def get_vaccinated_codes_for_patient(patient_id: int) -> set:
    """Get set of vaccine codes that have been administered for a patient."""
    session = get_session()
    try:
        records = session.query(VaccinationRecord).filter_by(patient_id=patient_id).all()
        codes = set()
        for r in records:
            vaccine = session.query(Vaccine).filter_by(id=r.vaccine_id).first()
            if vaccine:
                codes.add(vaccine.cod)
        return codes
    finally:
        session.close()


def get_all_vaccines() -> list:
    """Retrieve all vaccines from the reference table."""
    session = get_session()
    try:
        vaccines = session.query(Vaccine).order_by(Vaccine.target_age_days).all()
        return [{"id": v.id, "cod": v.cod, "nume": v.nume,
                 "target_age_days": v.target_age_days} for v in vaccines]
    finally:
        session.close()


def get_db_stats() -> dict:
    """Get database statistics for the dashboard."""
    session = get_session()
    try:
        total_patients = session.query(Patient).count()
        total_records = session.query(VaccinationRecord).count()
        return {
            "total_patients": total_patients,
            "total_vaccination_records": total_records,
        }
    finally:
        session.close()
