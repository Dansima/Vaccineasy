# Verification evidence and limits

Checked 1 October 2026 on Windows with Python 3.12 in the existing project virtual environment.

## Automated evidence

`python -m pytest -q`: **61 passed** after the presentation and label changes. Tests use temporary SQLite databases. Coverage includes CNP parsing/checksum tolerance, age and exact boundaries, month-end/leap-year arithmetic, multiple pending vaccines/status priority, historical recording membership, CSV/XLSX import and rollback, unique/atomic storage, baseline persistence, retained metadata and deleted-dose persistence, patient switching/future disabled controls, and workbook structure/content/pagination.

New presentation checks prove the English display frame does not mutate the Romanian reporting data and that injected patient HTML is escaped while user-entered notes remain unchanged. Streamlit checks also assert the four English tabs and the original Overdue/Due filter default.

SHA-256 comparison against [the saved pre-redesign baseline](preservation-baseline.json) passed for business_logic.py, database.py, models.py, reporting.py and excel_exporter.py. Changes to those files visible relative to Git predate this redesign; they were not introduced by this UI task. No database migration, clinical rule change or subscription integration was added.

## Browser checks

The app ran on loopback port 8502 against `tmp/ui-preview-data`, completely separate from the practice database. Four clearly synthetic identities (DEMO-ID values, not real CNPs) exercise overdue, due, upcoming and up-to-date states. Checks covered:

- Overview status counts, English filters and multiple pending-dose display.
- Selecting/checking/saving an eligible synthetic dose; success feedback and updated history.
- Future disabled doses and prominent patient identity in the existing form.
- Patient history with confirmed-dose indication and full-record table.
- September historical reference date, changed ages/status and visible historical warning.
- Monthly preview and actual XLSX download; openpyxl inspection confirmed `Pagina 1`, Romanian title/reference-month header and synthetic patient rows.
- Standard viewport and 768-pixel width. Narrow views need horizontal scrolling for tab/table content; this is primarily a desktop workspace. Metric labels wrap rather than truncate. Viewport override was reset.

Visual inspection caught and corrected faint helper text, a clipped eyebrow heading, narrow metric truncation, historical-warning contrast and upload-limit contrast. Native Streamlit widgets/dataframes retain their own interaction behavior.

Screenshots: [overview](screenshots/overview.jpg), [recording](screenshots/record.jpg), [history](screenshots/history.jpg), [monthly report](screenshots/report.jpg), [historical view](screenshots/historical.jpg), [narrow view](screenshots/narrow.jpg). All contain synthetic records only. Screenshots illustrate separate stages of the demonstration, so record totals can differ after a synthetic save.

## Unverified areas

No physical macOS/Apple Silicon install, Docker engine build, signed-installer/update path, representative practitioner usability session, formal accessibility audit, screen-reader study, independent penetration test or complete runtime network audit was performed. No real patient import/edit was used for UI verification. Clinical and administrative acceptance of assumptions, schedule scope and workbook remain external review gates.

Streamlit emits existing `use_container_width` deprecation warnings with the installed runtime. They did not fail tests; changing the supported dependency floor and migrating those calls should be part of release packaging validation. Requirements remain broadly versioned and need a tested release lock. This evidence does not establish GDPR, MDR, WCAG or clinical compliance.

## Source package

`Vaccineasy-macOS.zip` is a refreshed cross-platform **source archive**, not a Mac installer. It includes English docs, app, tests and launch/configuration files. It excludes the virtual environment, Git metadata, patient databases, temporary synthetic databases, uploads, the supplied reference PDF and local logs. Create a fresh virtual environment on the target device. Physical-device verification is still required before marketing platform support.

## Search-field follow-up

The Desktop installation uses Streamlit 1.55.0; the original workspace preview used 1.64.0. Keyboard checks were repeated with the Desktop interpreter and source against a separate synthetic database. Ctrl+A selected the complete typed query; typing replaced it and Backspace cleared it in the status and patient dropdown searches. The table's native search also replaced `Demo` with `Patient B` using Ctrl+A and returned one matching result.

The stylesheet applied a custom blue outline to dropdowns' small internal inputs, making focus look like a separate text-selection box. Removed that inner outline, applied one neutral focus border to the whole field, and changed selected text to a gray highlight. No keyboard interception or widget replacement was introduced. Updated `app/styles.css` in the user's Desktop project; refresh the app page to load it. [Screenshot with synthetic data](screenshots/search-field.jpg).
