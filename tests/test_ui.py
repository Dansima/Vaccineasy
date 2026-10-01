from datetime import date
from pathlib import Path
from streamlit.testing.v1 import AppTest
from app.business_logic import as_datetime, get_exact_due_date
from tests.test_database import add_patient

APP = str(Path(__file__).resolve().parents[1] / 'app' / 'main.py')


def test_empty_app(isolated_db):
    app = AppTest.from_file(APP, default_timeout=20).run()
    assert not app.exception
    assert len(app.tabs) == 4
    assert len(app.metric) == 6
    assert [tab.label for tab in app.tabs] == ['Overview', 'Record vaccination', 'Patient history', 'Monthly report']
    assert app.multiselect[0].value == ['🔴 RESTANT', '🟡 Scadent']


def test_form_patient_switch_and_historical_mode(isolated_db):
    db = isolated_db
    dob = get_exact_due_date(as_datetime(), -6).date()
    first = add_patient(db, dob, '5250101123456')
    second = add_patient(db, dob, '6250101123456')
    db.record_vaccination(first, 'Hexa_2', date.today())
    app = AppTest.from_file(APP, default_timeout=20).run()
    assert not app.exception
    assert app.checkbox(key=f'vaccine_{first}_Hexa_2').value
    app.selectbox(key='record_patient').select(second).run()
    assert not app.exception
    assert not app.checkbox(key=f'vaccine_{second}_Hexa_2').value
    app.checkbox(key=f'vaccine_{second}_Hexa_2').check()
    next(b for b in app.button if b.label == 'Save vaccination changes').click().run()
    assert not app.exception
    assert db.get_vaccinated_codes_for_patient(second) == {'Hexa_2'}
    app.checkbox(key=f'vaccine_{second}_Hexa_2').uncheck()
    next(b for b in app.button if b.label == 'Save vaccination changes').click().run()
    assert not app.exception and db.get_vaccinated_codes_for_patient(second) == set()
    app.date_input[0].set_value(dob).run()
    assert not app.exception
    assert any('Historical view' in w.value for w in app.warning)
