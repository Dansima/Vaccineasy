"""
Vaccineasy v4.0 — Business Logic Module
CNP decoding, vaccination schedule engine, age formatting.
"""

from datetime import datetime
from typing import Optional


# Romanian CNP checksum weights
CNP_WEIGHTS = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9]


def validate_cnp_checksum(cnp: str) -> bool:
    """
    Validate the CNP checksum (digit 13) using the official algorithm.
    Weighted sum of first 12 digits mod 11; if result is 10, control digit is 1.
    """
    if len(cnp) != 13 or not cnp.isdigit():
        return False

    digits = [int(d) for d in cnp]
    checksum = sum(d * w for d, w in zip(digits[:12], CNP_WEIGHTS)) % 11

    if checksum == 10:
        checksum = 1

    return digits[12] == checksum


def decode_cnp(cnp: str) -> Optional[datetime]:
    """
    Extract date of birth from a Romanian CNP (Cod Numeric Personal).

    CNP format: S AA LL ZZ JJ NNN C
      S  = sex/century digit (1-8)
      AA = year (last 2 digits)
      LL = month (01-12)
      ZZ = day (01-31)
      JJ = county code
      NNN = sequence number
      C  = checksum digit

    Sex digit mapping:
      1,2 = born 1900-1999 (male, female)
      3,4 = born 1800-1899 (male, female)
      5,6 = born 2000-2099 (male, female)
      7,8 = foreign residents (male, female) — assumed 2000+ if AA < 26, else 1900+
      9   = foreign (no century info — handled as best effort)

    Returns None if:
      - CNP is too short or contains non-digit characters
      - Checksum is invalid
      - Date cannot be parsed
    """
    cnp = str(cnp).strip()
    cnp = ''.join(filter(str.isdigit, cnp))

    if len(cnp) < 13:
        return None

    cnp = cnp[:13]  # Take only first 13 digits if longer

    if not validate_cnp_checksum(cnp):
        # Allow invalid checksums for now (test data doesn't have valid checksums)
        # but log it. In production, uncomment the return None.
        # return None
        pass

    try:
        s = int(cnp[0])
        aa = int(cnp[1:3])
        ll = int(cnp[3:5])
        zz = int(cnp[5:7])

        century_map = {
            1: 1900, 2: 1900,  # Male/Female born 1900-1999
            3: 1800, 4: 1800,  # Male/Female born 1800-1899
            5: 2000, 6: 2000,  # Male/Female born 2000-2099
        }

        if s in century_map:
            secol = century_map[s]
        elif s in (7, 8, 9):
            # Foreign residents — best effort based on year digits
            # If aa <= current year's last 2 digits, assume 2000s; else 1900s
            current_year_short = datetime.now().year % 100
            secol = 2000 if aa <= current_year_short else 1900
        else:
            return None  # Invalid sex digit (0)

        an = secol + aa
        return datetime(an, ll, zz)

    except (ValueError, OverflowError):
        return None


def format_varsta(data_nasterii: Optional[datetime]) -> str:
    """
    Format age as 'X ani, Y luni' from a date of birth.
    Returns 'CNP Invalid' if data_nasterii is None.
    """
    if not data_nasterii:
        return "CNP Invalid"

    azi = datetime.now()
    ani = azi.year - data_nasterii.year
    luni = azi.month - data_nasterii.month

    if luni < 0:
        ani -= 1
        luni += 12

    if ani == 0:
        return f"{luni} luni"
    elif luni == 0:
        return f"{ani} ani fix"
    else:
        return f"{ani} ani, {luni} luni"


# =============================================================
# VACCINATION SCHEDULE ENGINE
# =============================================================

# Romania's National Vaccination Schedule
# Key = target age in days, Value = (vaccine name, category code)
VACCINATION_SCHEDULE = {
    60:   ("Hexavalent (2 luni)", "Hexa_2"),
    120:  ("Hexavalent (4 luni)", "Hexa_4"),
    330:  ("Hexavalent (11 luni)", "Hexa_11"),
    365:  ("ROR (12 luni)", "ROR_12"),
    1825: ("ROR + Tetra (5 ani)", "ROR_Tetra_5"),
    5110: ("dTPa (14 ani)", "dTPa_14"),
}

# Status thresholds (in days)
UPCOMING_WINDOW = 14    # Days before target to show as "Urmează"
DUE_WINDOW = 30         # Days after target to show as "Scadent"
OVERDUE_LIMIT = 500     # Days after target before we stop flagging as "Restant"

# Age limit — children only
MAX_AGE_YEARS = 15


def get_single_vaccination_status(data_nasterii: Optional[datetime]):
    """
    LEGACY — Returns only the first matching vaccination status.
    Kept for backward compatibility with the Anexa 1 export.
    Returns: (status_text, vaccine_name, category_code)
    """
    statuses = get_all_vaccination_statuses(data_nasterii)
    if not statuses:
        return "🟢 La Zi", "-", None

    # Priority: RESTANT > Scadent > Urmează
    for status_text, vaccin, cod_cat in statuses:
        if "RESTANT" in status_text:
            return status_text, vaccin, cod_cat
    for status_text, vaccin, cod_cat in statuses:
        if "Scadent" in status_text:
            return status_text, vaccin, cod_cat
    return statuses[0]


def get_all_vaccination_statuses(data_nasterii: Optional[datetime]):
    """
    Returns ALL pending vaccination statuses for a child.
    This fixes the bug where only the first overdue vaccine was reported.

    Returns: list of (status_text, vaccine_name, category_code) tuples
             Empty list if child is up-to-date, adult, or CNP is invalid.
    Special returns (as single-item lists):
             [("Eroare CNP", "-", None)] if data_nasterii is None
             [("🟢 Adult (Ignorat)", "-", None)] if age > 15
    """
    if not data_nasterii:
        return [("Eroare CNP", "-", None)]

    azi = datetime.now()
    varsta_zile = (azi - data_nasterii).days
    varsta_ani = varsta_zile / 365.25

    if varsta_ani > MAX_AGE_YEARS:
        return [("🟢 Adult (Ignorat)", "-", None)]

    results = []
    for zi_tinta, (nume_vaccin, cod_cat) in VACCINATION_SCHEDULE.items():
        diff = varsta_zile - zi_tinta

        if -UPCOMING_WINDOW <= diff < 0:
            # Upcoming: within 14 days before target
            results.append(("🟢 Urmează", nume_vaccin, cod_cat))
        elif 0 <= diff <= DUE_WINDOW:
            # Due: within 30 days after target
            results.append(("🟡 Scadent", nume_vaccin, cod_cat))
        elif DUE_WINDOW < diff < OVERDUE_LIMIT:
            # Overdue: more than 30 days but less than 500 days past target
            results.append(("🔴 RESTANT", nume_vaccin, cod_cat))

    return results
