import sys
import os

# Adaugam calea curenta in sys.path
sys.path.append(os.getcwd())

from app.database import get_session, _auto_vaccinate_patient, Patient
from datetime import datetime

def test_heal():
    session = get_session()
    try:
        patients = session.query(Patient).all()
        print(f"Testing heal for {len(patients)} patients")
        for p in patients:
            if p.data_nasterii:
                dn = datetime.combine(p.data_nasterii, datetime.min.time())
                try:
                    _auto_vaccinate_patient(session, p.id, dn)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
        session.commit()
        print("Heal process executed and committed.")
    except Exception as e:
        session.rollback()
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    test_heal()
