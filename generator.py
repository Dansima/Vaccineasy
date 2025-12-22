import pandas as pd
import random
from datetime import datetime, timedelta


def generare_pacienti_fictivi(total=2000):
    print(f"Generare {total} de pacienți... Te rog așteaptă.")

    nume_familie = ["Popescu", "Ionescu", "Radu", "Dumitru", "Stan", "Stoica", "Gheorghe", "Dinu", "Serban", "Matei",
                    "Constantin", "Toma", "Dobre", "Ene", "Mocanu"]
    prenume_baieti = ["Andrei", "Alexandru", "Gabriel", "Ionut", "Stefan", "David", "Mihai", "Cristian", "Darius",
                      "Luca"]
    prenume_fete = ["Maria", "Elena", "Ioana", "Andreea", "Sofia", "Antonia", "Alexandra", "Gabriela", "Daria", "Eva"]

    data = []
    azi = datetime.now()

    # Configurare proporții: 75% Adulți (de ignorat), 25% Copii (de procesat)
    target_adulti = int(total * 0.75)

    for i in range(total):
        # 1. Alegem dacă e Adult sau Copil
        if i < target_adulti:
            # Generăm Adult (19 - 80 ani)
            zile_varsta = random.randint(7000, 29000)
        else:
            # Generăm Copil (0 - 15 ani / aprox 5500 zile)
            zile_varsta = random.randint(1, 5500)

        data_nasterii = azi - timedelta(days=zile_varsta)

        # 2. Generăm Sexul (pentru Nume și CNP)
        is_male = random.choice([True, False])

        if is_male:
            nume = f"{random.choice(nume_familie)} {random.choice(prenume_baieti)}"
            # Sex 1 (1900-1999) sau 5 (2000-2099)
            sex_digit = "1" if data_nasterii.year < 2000 else "5"
        else:
            nume = f"{random.choice(nume_familie)} {random.choice(prenume_fete)}"
            # Sex 2 (1900-1999) sau 6 (2000-2099)
            sex_digit = "2" if data_nasterii.year < 2000 else "6"

        # 3. Construim CNP Valid (Sex + AA + LL + ZZ + Random)
        aa = str(data_nasterii.year)[-2:]
        ll = f"{data_nasterii.month:02d}"
        zz = f"{data_nasterii.day:02d}"
        rest_cnp = f"{random.randint(100000, 999999)}"  # 6 cifre random la final

        cnp = f"{sex_digit}{aa}{ll}{zz}{rest_cnp}"

        data.append({
            "Nume si Prenume": nume,
            "CNP": cnp,
            "Telefon": f"07{random.randint(20000000, 99999999)}"  # Optional
        })

    # Creăm DataFrame
    df = pd.DataFrame(data)

    # Salvăm Excel
    nume_fisier = "pacienti_2000.xlsx"
    df.to_excel(nume_fisier, index=False)
    print(f"✅ Gata! Fișierul '{nume_fisier}' a fost creat cu succes.")
    print(f"   - Adulți generați: ~{target_adulti}")
    print(f"   - Copii generați: ~{total - target_adulti}")


if __name__ == "__main__":
    # Verificăm dacă avem librăria openpyxl pentru scriere Excel
    try:
        import openpyxl

        generare_pacienti_fictivi(2000)
    except ImportError:
        print("Eroare: Îți lipsește librăria 'openpyxl'.")
        print("Scrie în consolă: pip install openpyxl")