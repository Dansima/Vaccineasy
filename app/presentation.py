"""English display adapters. Stored values and clinical calculations stay unchanged."""
import re
from html import escape

from app.business_logic import format_varsta

STATUS_LABELS = {
    '🔴 RESTANT': 'Overdue', '🟡 Scadent': 'Due',
    '🟢 Urmează': 'Upcoming', '🟢 La Zi': 'Up to date',
    '🟢 Adult (Ignorat)': 'Outside the pediatric age range', 'Eroare CNP': 'Invalid birth date',
}
VACCINE_LABELS = {
    'Hexa_2': 'Hexavalent · 2 months', 'Hexa_4': 'Hexavalent · 4 months',
    'Hexa_11': 'Hexavalent · 11 months', 'ROR_12': 'MMR · 12 months',
    'ROR_Tetra_5': 'MMR · 5 years', 'Tetra_6': 'DTaP-IPV · 6 years',
    'dTPa_14': 'Tdap · 14 years',
}
MONTHS = ('January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December')


def display_date(value):
    return f'{value.day:02d} {MONTHS[value.month - 1]} {value.year}'


def display_age(dob, reference_date=None):
    value = format_varsta(dob, reference_date)
    if value == 'CNP Invalid':
        return 'Birth date unavailable'
    if value == 'Nenăscut la data de referință':
        return 'Not born on the reference date'
    value = value.replace(' ani fix', ' years').replace(' ani', ' years').replace(' luni', ' months')
    return re.sub(r'\b1 years\b', '1 year', re.sub(r'\b1 months\b', '1 month', value))


def display_note(value):
    """Translate only application-generated notes; preserve user-entered text."""
    if value == 'Auto-înregistrat la import — presupus, neconfirmat clinic':
        return 'Assumed at import; not clinically confirmed'
    if value == 'Auto-înregistrat la import':
        return 'Automatically recorded at import'
    if value == 'Înregistrat manual':
        return 'Recorded manually'
    return value


def display_error(value):
    messages = {
        'Pacientul nu este eligibil pentru acest formular.': 'This patient is not eligible for this form.',
        'Cod de vaccin necunoscut.': 'The vaccine code was not recognized. Reload and try again.',
        'Vaccinul nu este încă scadent.': 'This vaccine is not yet due. No changes were saved.',
        'Importul a fost anulat integral din cauza unei erori de salvare.':
            'The import was rolled back after a storage error. No changes were saved.',
        'Format acceptat: XLSX, XLS sau CSV.': 'Choose an XLSX, XLS or CSV file.',
        'Fișierul conține coloane duplicate.': 'The file contains duplicate column names.',
        'Sunt necesare coloanele Nume, Prenume, CNP.':
            'Required ICMED columns are missing: Nume, Prenume, CNP.',
    }
    if value in messages:
        return messages[value]
    if value.startswith('Fișierul nu poate fi citit: '):
        detail = value.removeprefix('Fișierul nu poate fi citit: ')
        return 'The file could not be read. ' + messages.get(
            detail, 'Check its format and export it again from ICMED.')
    match = re.fullmatch(r'Rândul (\d+): CNP, dată de naștere sau nume invalid\.', value)
    if match:
        return f'Row {match[1]} was skipped: invalid CNP, birth date or name.'
    return 'The operation could not be completed. Check the input and try again.'


def display_patient_frame(frame, include_status=True):
    """Return a display-only copy, leaving the export's Romanian contract intact."""
    result = frame[['Nume si Prenume', 'CNP', 'Vârsta', 'Vaccin Necesar', 'Status']].copy()
    result['Vaccin Necesar'] = frame['_pending'].map(
        lambda pending: ', '.join(VACCINE_LABELS[code] for _, _, code in pending) or 'None pending')
    result['Vârsta'] = result['Vârsta'].map(
        lambda text: re.sub(r'\b1 years\b', '1 year', re.sub(r'\b1 months\b', '1 month',
            text.replace(' ani fix', ' years').replace(' ani', ' years').replace(' luni', ' months'))))
    result['Status'] = result['Status'].map(STATUS_LABELS)
    result = result.rename(columns={'Nume si Prenume': 'Patient', 'CNP': 'CNP',
                                   'Vârsta': 'Age', 'Vaccin Necesar': 'Pending vaccines'})
    return result if include_status else result[['Patient', 'CNP', 'Pending vaccines']]


def patient_context_html(patient, reference_date=None):
    dob = patient['data_nasterii']
    return (
        '<section class="patient-context" aria-label="Selected patient">'
        '<div class="eyebrow">Selected patient</div>'
        f'<h3>{escape(patient["nume"])}</h3>'
        '<div class="patient-facts">'
        f'<span><b>CNP</b> {escape(patient["cnp"])}</span>'
        f'<span><b>Born</b> {display_date(dob) if dob else "Unavailable"}</span>'
        f'<span><b>Age</b> {display_age(dob, reference_date)}</span>'
        '</div></section>'
    )
