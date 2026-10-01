from datetime import date, datetime, timedelta
import pytest
from app.business_logic import (
    decode_cnp, validate_cnp_checksum, format_varsta, get_exact_due_date,
    get_all_vaccination_statuses, get_single_vaccination_status, is_child,
    VACCINATION_SCHEDULE,
)


@pytest.mark.parametrize('cnp,expected', [
    ('1900315123456', datetime(1990, 3, 15)), ('2850722123456', datetime(1985, 7, 22)),
    ('5240110123456', datetime(2024, 1, 10)), ('6251201123456', datetime(2025, 12, 1)),
    ('3800615123456', datetime(1880, 6, 15)), ('4800615123456', datetime(1880, 6, 15)),
    ('1 90-03-15 123456', datetime(1990, 3, 15)),
    ('7240510123456', datetime(2024, 5, 10)), ('8240510123456', datetime(2024, 5, 10)),
    ('9990510123456', datetime(1999, 5, 10)), ('0900315123456', None),
    ('', None), ('123', None), (None, None), ('5240230123456', None), ('52401101234567', None),
])
def test_decode(cnp, expected):
    assert decode_cnp(cnp) == expected


def test_foreign_century_boundary():
    yy = datetime.now().year % 100
    assert decode_cnp(f'7{yy:02d}0101123456').year == 2000 + yy
    assert decode_cnp(f'8{yy+1:02d}0101123456').year == 1900 + yy + 1


@pytest.mark.parametrize('cnp,expected', [
    ('1800101221144', True), ('1800101221145', False),
    ('5000101000091', True),  # weighted sum 98 -> remainder 10 -> control 1
    ('12345', False), ('123456789ABCD', False), (None, False),
])
def test_checksum(cnp, expected):
    assert validate_cnp_checksum(cnp) is expected


def test_bad_checksum_still_decodes():
    assert decode_cnp('1800101221145') == datetime(1980, 1, 1)


@pytest.mark.parametrize('dob,ref,expected', [
    (None, date(2026, 1, 1), 'CNP Invalid'),
    (date(2025, 10, 1), date(2026, 1, 1), '3 luni'),
    (date(2020, 10, 1), date(2025, 10, 1), '5 ani fix'),
    (date(2020, 8, 1), date(2025, 10, 1), '5 ani, 2 luni'),
    (date(2025, 8, 20), date(2025, 10, 19), '1 luni'),
    (date(2025, 1, 31), date(2025, 2, 28), '1 luni'),
    (date(2026, 1, 2), date(2026, 1, 1), 'Nenăscut la data de referință'),
])
def test_age(dob, ref, expected):
    assert format_varsta(dob, ref) == expected


@pytest.mark.parametrize('dob,months,expected', [
    (date(2025, 1, 31), 1, datetime(2025, 2, 28)),
    (date(2024, 1, 31), 1, datetime(2024, 2, 29)),
    (date(2024, 2, 29), 12, datetime(2025, 2, 28)),
    (date(2025, 12, 31), 2, datetime(2026, 2, 28)),
])
def test_due_dates(dob, months, expected):
    assert get_exact_due_date(dob, months) == expected


@pytest.mark.parametrize('offset,status', [(-32, None), (-31, 'Urmează'), (-1, 'Urmează'),
                                        (0, 'Scadent'), (30, 'Scadent'), (31, 'RESTANT')])
def test_status_boundaries(offset, status):
    ref = datetime(2025, 3, 1) + timedelta(days=offset, hours=23)
    hexa = [s for s, _, code in get_all_vaccination_statuses(datetime(2025, 1, 1), ref) if code == 'Hexa_2']
    assert (status in hexa[0]) if status else not hexa


def test_multiple_priority_and_completed():
    dob, ref = datetime(2025, 1, 1), datetime(2026, 1, 1)
    statuses = get_all_vaccination_statuses(dob, ref)
    assert {'Hexa_2', 'Hexa_4', 'Hexa_11', 'ROR_12'} <= {c for _, _, c in statuses}
    assert 'RESTANT' in get_single_vaccination_status(dob, ref)[0]
    assert 'Scadent' in get_single_vaccination_status(dob, ref, {'Hexa_2', 'Hexa_4', 'Hexa_11'})[0]
    assert get_single_vaccination_status(dob, ref, {c for _, c in VACCINATION_SCHEDULE.values()})[0] == '🟢 La Zi'


def test_adult_invalid_and_newborn():
    ref = datetime(2026, 1, 1)
    assert 'Adult' in get_single_vaccination_status(datetime(2000, 1, 1), ref)[0]
    assert 'Eroare' in get_single_vaccination_status(None, ref)[0]
    assert not get_all_vaccination_statuses(ref, ref)
    assert is_child(date(2011, 1, 1), ref)
    assert not is_child(date(2010, 12, 31), ref)
    assert not is_child(date(2026, 1, 2), ref)
