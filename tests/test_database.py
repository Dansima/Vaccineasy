from datetime import datetime, date
from io import BytesIO
import pandas as pd
import pytest
from app.models import Patient, ImportBaseline
from app.business_logic import as_datetime, get_exact_due_date
from app.reporting import build_operative_list


def upload(content, name='patients.csv'):
    stream = BytesIO(content.encode('utf-8') if isinstance(content, str) else content)
    stream.name = name
    return stream


def add_patient(db, dob=date(2025, 1, 1), cnp='5250101123456'):
    with db.get_session() as session, session.begin():
        p = Patient(cnp=cnp, nume='Pacient Test', data_nasterii=dob)
        session.add(p)
        session.flush()
        session.add(ImportBaseline(patient_id=p.id, cutoff_date=date.today()))
        return p.id


def test_import_upsert_and_invalid_rows(isolated_db):
    db = isolated_db
    content = 'Nume;Prenume;CNP;Telefon\nPop;Ana;6250101123456;0712345678\nPop;Dan;invalid;\n'
    result = db.import_patients_from_excel(upload(content))
    assert (result['imported'], result['skipped']) == (1, 1)
    result = db.import_patients_from_excel(upload(content.replace('Ana', 'Maria')))
    assert result['updated'] == 1
    p = db.get_all_patients()[0]
    assert p['nume'] == 'Pop Maria' and p['telefon'] == '0712345678'
    assert db.get_db_stats()['total_patients'] == 1


def test_numeric_excel_and_missing_cnp(isolated_db):
    buffer = BytesIO()
    pd.DataFrame({'Nume': ['Test', 'Lipsă'], 'Prenume': ['Copil', 'CNP'],
                  'CNP': [5250101123456, None]}).to_excel(buffer, index=False)
    result = isolated_db.import_patients_from_excel(upload(buffer.getvalue(), 'ICMED.XLSX'))
    assert result['imported'] == 1 and result['skipped'] == 1
    assert isolated_db.get_all_patients()[0]['cnp'] == '5250101123456'


def test_missing_columns(isolated_db):
    result = isolated_db.import_patients_from_excel(upload('Nume,CNP\nTest,5250101123456\n'))
    assert result['errors'] and result['imported'] == 0


def test_baseline_and_persistent_deletion(isolated_db):
    db = isolated_db
    with db.get_session() as session, session.begin():
        p = Patient(cnp='5250101123456', nume='Test', data_nasterii=date(2025, 1, 1))
        session.add(p)
        session.flush()
        pid = p.id
        db._auto_vaccinate_patient(session, pid, p.data_nasterii, datetime(2025, 5, 15))
    history = db.get_vaccination_history(pid)
    assert [r['vaccine_cod'] for r in history] == ['Hexa_2']
    assert history[0]['assumed'] and history[0]['date_administered'] == date(2025, 3, 1)
    db.delete_vaccination_record(history[0]['id'])
    db.init_db()
    assert db.get_vaccination_history(pid) == []


def test_reference_date_excludes_later_administrations(isolated_db):
    db = isolated_db
    pid = add_patient(db)
    assert db.record_vaccination(pid, 'Hexa_2', date(2025, 4, 1))['success']
    assert db.get_vaccinated_codes_for_patient(pid, date(2025, 3, 15)) == set()
    assert db.get_vaccinated_codes_for_patient(pid, date(2025, 4, 1)) == {'Hexa_2'}
    assert 'Hexa_2' in build_operative_list(date(2025, 3, 15)).iloc[0]['_all_codes']
    assert 'Hexa_2' not in build_operative_list(date(2025, 4, 1)).iloc[0]['_all_codes']


def test_historical_child_and_unborn(isolated_db):
    db = isolated_db
    pid = add_patient(db, date(2008, 1, 1), '5080101123456')
    assert not db.get_children_patients(date(2026, 1, 1))
    assert db.get_children_patients(date(2020, 1, 1))[0]['id'] == pid
    assert not db.get_children_patients(date(2007, 1, 1))


def test_atomic_form_preserves_dates_and_deletions(isolated_db):
    db = isolated_db
    dob = get_exact_due_date(as_datetime(), -6).date()
    pid = add_patient(db, dob)
    first = get_exact_due_date(dob, 2).date()
    db.record_vaccination(pid, 'Hexa_2', first, lot_number='Lot vechi')
    db.save_vaccination_selection(pid, {'Hexa_2', 'Hexa_4'}, 'Lot nou', 'Medic Test')
    history = {r['vaccine_cod']: r for r in db.get_vaccination_history(pid)}
    assert history['Hexa_2']['date_administered'] == first
    assert history['Hexa_2']['lot_number'] == 'Lot vechi'
    assert history['Hexa_4']['date_administered'] == date.today()
    with pytest.raises(ValueError):
        db.save_vaccination_selection(pid, {'ROR_12'})
    assert len(db.get_vaccination_history(pid)) == 2
    db.save_vaccination_selection(pid, {'Hexa_4'})
    db.init_db()
    assert db.get_vaccinated_codes_for_patient(pid) == {'Hexa_4'}


def test_crud_and_unique_constraint(isolated_db):
    db = isolated_db
    pid = add_patient(db)
    db.record_vaccination(pid, 'Hexa_2', date(2025, 3, 1))
    db.record_vaccination(pid, 'Hexa_2', date(2025, 3, 2))
    assert len(db.get_vaccination_history(pid)) == 1
    assert db.delete_patient(pid)
    assert db.get_db_stats() == dict(total_patients=0, total_vaccination_records=0)


def test_failed_import_counts_committed_rows_only(isolated_db, monkeypatch):
    def fail(*args):
        raise RuntimeError('simulated database error')
    monkeypatch.setattr(isolated_db, '_auto_vaccinate_patient', fail)
    result = isolated_db.import_patients_from_excel(upload('Nume,Prenume,CNP\nTest,Ana,6250101123456\n'))
    assert result['imported'] == result['updated'] == 0 and result['errors']
    assert isolated_db.get_all_patients() == []
