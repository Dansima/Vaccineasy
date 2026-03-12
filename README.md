# 💉 Vaccineasy v4.0

Sistem de management vaccinări pediatrice conform Calendarului Național de Vaccinare din România.

## Funcționalități

- **Import pacienți** din Excel/CSV (exportat din ICMED)
- **Decodare CNP** automată → extrage data nașterii
- **Motor de vaccinare** → identifică restanțieri, scadenți, și viitoare vaccinări
- **Înregistrare vaccinări** → salvează data, lotul, și cine a administrat
- **Istoric pacient** → vizualizare completă per pacient
- **Export Anexa 1** → catagrafie oficială paginată (13 rânduri/pagină)
- **Bază de date SQLite** → datele se păstrează local

## Cerințe

- Docker & Docker Compose
- Sau: Python 3.11+ (pentru development local)

## Instalare cu Docker (recomandat)

```bash
# Clonează repositoriul
git clone https://github.com/Dansima/Vaccineasy.git
cd Vaccineasy

# Construiește și pornește
docker compose up -d --build

# Deschide în browser
# http://localhost:8501
```

## Development local (fără Docker)

```bash
# Creează virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalează dependențele
pip install -r requirements.txt

# Rulează aplicația
streamlit run app/main.py
```

## Structura Proiectului

```
app/
├── main.py              # Interfața Streamlit (UI)
├── business_logic.py    # Decodare CNP, motor vaccinare
├── database.py          # Operații SQLite
├── models.py            # Modele SQLAlchemy
└── excel_exporter.py    # Generator Anexa 1

tests/                   # Teste automate
docker/                  # Dockerfile
data/                    # Baza de date SQLite (auto-creat)
```

## Teste

```bash
pip install pytest
python -m pytest tests/ -v
```

## Licență

Uz intern — date medicale confidențiale.
