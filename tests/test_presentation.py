from copy import deepcopy
from datetime import date, datetime

from pandas.testing import assert_frame_equal
from app.presentation import display_patient_frame, patient_context_html, display_note
from app.reporting import build_operative_list
from tests.test_database import add_patient


def test_english_display_preserves_reporting_contract(isolated_db):
    add_patient(isolated_db, date(2025, 1, 1))
    frame = build_operative_list(datetime(2025, 6, 1))
    original = deepcopy(frame)
    displayed = display_patient_frame(frame)
    assert displayed.iloc[0]['Status'] == 'Overdue'
    assert displayed.iloc[0]['Pending vaccines'] == 'Hexavalent · 2 months, Hexavalent · 4 months'
    assert displayed.iloc[0]['Age'] == '5 months'
    assert_frame_equal(frame, original)
    assert frame.iloc[0]['Status'] == '🔴 RESTANT'


def test_patient_identity_is_escaped_and_user_notes_preserved():
    card = patient_context_html({'nume': '<img src=x onerror=alert(1)>',
        'cnp': '<script>1</script>', 'data_nasterii': date(2025, 1, 1)}, datetime(2026, 1, 1))
    assert '<img' not in card and '<script>' not in card
    assert '&lt;img' in card and '&lt;script&gt;' in card
    assert '1 year' in card
    assert display_note('Notă introdusă de medic') == 'Notă introdusă de medic'
