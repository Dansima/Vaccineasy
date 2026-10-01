# Vaccineasy

Vaccineasy is a local vaccination workspace for Romanian family practices. It imports an ICMED patient list, calculates pediatric vaccination status, records administrations, displays patient history, and generates the Romanian Anexa 1 monthly workbook. The interface and documentation are English; official report headings and ICMED source column names remain Romanian.

This is runnable source software, not a signed commercial installer. Subscription management is not implemented. Review the clinical assumptions and security gaps before using it with practice records.

## Getting started

Use Python 3.11 or later. Extract the project to a private local folder and run commands from that folder. Installing Python and dependencies initially requires internet; the current application has no cloud service dependency at runtime.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run.ps1
```

If your managed computer blocks PowerShell scripts, use the equivalent command from the project root:

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe -m streamlit run app/main.py
```

### MacBook / macOS and Linux

Install a Python 3.11+ build appropriate for your operating system and processor. A Mac uses the macOS commands, not run.ps1 or a copied Windows virtual environment. Create its environment locally:

```bash
cd /path/to/Vaccineasy
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=. .venv/bin/python -m streamlit run app/main.py
```

Open [the local app](http://127.0.0.1:8501) in your browser. Keep the terminal open; Ctrl+C stops the app. These commands have been verified on Windows in this workspace; physical Mac/Apple Silicon installation still needs release testing. Compatibility with every laptop is not guaranteed.

### Docker

```bash
docker compose up -d --build
```

Compose publishes only 127.0.0.1:8501 and stores records in vaccineasy_data. `docker compose down` keeps the volume; `docker compose down -v` deletes it. Docker backup requires copying the volume through your Docker tooling; it is separate from the source folder's data directory.

## First session

1. Export an ICMED XLSX, XLS or CSV containing `Nume`, `Prenume`, `CNP`; `Telefon` is optional. Upload it and select **Import patients**. Review added, updated, skipped and error counts. The import matches patients by CNP.
2. Use **Overview** to review overdue and due children. The default filters remain Overdue and Due. All pending doses appear in each patient's row. Age and due dates are recalculated each time the app runs using the reference date; no annual reimport is needed.
3. In **Record vaccination**, check the patient's name, CNP and birth date. Check administered doses and optionally enter the batch and administrator. New records use today's real date. Unchanged checked doses retain their original metadata. Future doses are disabled. **Unchecking a dose deletes its record when saved.**
4. Use **Patient history** for schedule status as of the selected reference date and the complete remaining record history. Later administrations are excluded from historical status but remain visible in the full table.
5. Select **Monthly report**, review the preview and download Anexa 1. It includes unrecorded doses scheduled that month or overdue on the selected date, with 13 children per page, youngest first.

### Preserved clinical and reporting assumptions

First import assumes doses scheduled before the import month's first day completed. These records are marked **assumed, not clinically confirmed**, and use scheduled dates. Current-month doses remain pending. This affects status and reports. The one-time baseline marker prevents restarts or reimports from recreating removed records or closing new overdue doses. Existing patients are initialized using their original creation date. These rules have been preserved, not clinically revalidated.

Status windows: Upcoming in the 31 days before the scheduled date; Due on that date through day 30 after it; Overdue from day 31 after it. Children older than their 15th birthday are excluded, as are children not yet born on the reference date. CNP checksum errors remain tolerated when the birth date is parseable.

The schedule tracks hexavalent at 2/4/11 months, MMR at 12 months/5 years, DTaP-IPV at 6 years and Tdap at 14 years. The [Ministry calendar](https://www.ms.ro/media/documents/15_Poster_Calendar_National_Vaccinare.pdf) shows a 5–6-year interval for DTaP-IPV; this app retains its existing 6-year threshold. Pneumococcal doses mirror hexavalent only in export; BCG and birth hepatitis B are not tracked independently and their report columns stay empty. The status windows are application rules, not a catch-up prescribing protocol. Practice review of clinical scope and report acceptance is a release gate.

## Storage, backup and updates

SQLite is stored at data/vaccineasy.db; `VACCINEASY_DB_DIR` can specify a different directory before launch. Existing records are retained. No patient-upload or subscription API is implemented. Local storage does not provide authentication, application-level encryption or an audit trail.

For a manual source-installation backup, stop all app processes using the database and copy the complete data directory, including any SQLite WAL/SHM files, to a protected practice-controlled location. Avoid personal cloud-synced folders. Keep a second encrypted copy on another approved medium. Before updating, retain the previous source version and a stopped-app backup. Test restoration on a separate private copy; never overwrite the only good database. Automated backups and migration rollback are proposed, not implemented.

## Tests and documentation

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use temporary databases. See [verification](docs/VERIFICATION.md) for evidence and limits.

- [Application audit and UI rationale](docs/APPLICATION_AUDIT.md)
- [Security and subscription delivery assessment](docs/SECURITY_AND_DELIVERY.md)
- [Delivery and sales plan](docs/DELIVERY_AND_SALES_PLAN.md)
- [Recommendations awaiting approval](docs/RECOMMENDATIONS.md)
- [Linear backlog](docs/LINEAR_BACKLOG.md)

## Structure

main.py and styles.css provide the Streamlit workspace; presentation.py translates display values without changing stored data. business_logic.py handles CNP, age and schedules; database.py and models.py handle SQLAlchemy/SQLite; reporting.py supplies shared status/report data; excel_exporter.py preserves the Romanian workbook. Tests cover unit, database, workbook and Streamlit behavior. Fonts resolve locally with Inter if installed and system sans-serif otherwise.
