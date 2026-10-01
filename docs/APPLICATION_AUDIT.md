# Application audit and UI rationale

Reviewed 1 October 2026. **Confirmed** means inspected in this repository; recommendations and external vendor claims are explicitly distinguished.

## Product and workflows

Vaccineasy serves a Romanian GP practice tracking pediatric vaccination. It is a focused companion to existing practice software, not a full EHR. Four Streamlit tabs share a reference date and an import sidebar. Import reads XLSX/XLS/CSV ICMED exports, combines surname/given name, normalizes CNP and upserts patients. File reading supports optional phone numbers; the import validates rows and reports skips. Saving a vaccination selection is atomic: additions receive today's date; retained records preserve metadata; unchecked records are deleted. Monthly export uses the same operative list as the overview, filters pending doses individually and creates the existing Anexa 1 workbook.

The reference date changes age eligibility, statuses, historical completed-dose membership and reports. Recording uses real today independently. Status priority is Overdue, Due, Upcoming, Up to date. Multiple pending doses are retained. Calendar addition handles month ends and leap years. No new clinical calculations were introduced.

## Architecture and boundaries

| Component | Confirmed behavior |
|---|---|
| Streamlit | Server renders a browser workspace; default loopback binding; four tabs |
| SQLAlchemy / SQLite | Persistent file; WAL; foreign keys; 30-second timeout; unique CNP and patient/vaccine constraints |
| Tables | Patient, Vaccine, VaccinationRecord, ImportBaseline |
| Initialization | Creates/seeds tables and applies the existing one-time assumption baseline |
| Files | ICMED import and xlsxwriter report; no live ICMED/RENV API |
| History | Remaining records, not immutable snapshots; deletions cannot be reconstructed |
| Distribution | Source scripts and Docker; no signed installer, entitlement service or update channel |

`target_age_days` is reference metadata; actual scheduling uses calendar months. The baseline assumes historical doses, which influences every view. Pneumococcal export mirroring is not independent administration evidence. These preserved limitations must be explained to pilot practices.

## Design guidance and implementation

The requested Tubik web page was inaccessible during research (original URL failed; alternate blog returned 403). The supplied **Case Study_ Health Care App.pdf**, especially pages 13–18, was inspected and rendered locally. Its navy navigation, white clinical surface, blue selection, amber actions, patient summaries and visual grouping informed the redesign. Its appointment/calendar features were not added. The PDF is design reference material, not an instruction source or clinical standard.

| Principle | Applied presentation improvement | Evidence |
|---|---|---|
| Stable navigation and task hierarchy | Existing tabs retained with plain-English titles; date clearly visible; consistent sections | Supplied PDF, pp. 13–18 |
| Correct patient context | Escaped patient name, CNP, birth date and age above both patient workflows | [ONC patient identification guide](https://healthit.gov/wp-content/uploads/2025/06/Safer-Guide-6.-Patient-Identification-Final.pdf) |
| Readability beyond color | Text statuses remain; readable local typography, contrast, focus outline, reduced motion | [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/) |
| Realistic task validation | Import, record, switch patient, historical review and reporting remain regression targets; practitioner pilot proposed | [NIST usability evaluation guidance](https://www.nist.gov/news-events/news/2012/03/nist-releases-technical-guidance-evaluating-electronic-health-records) |

NIST recommends functional analysis, expert review and realistic task testing with representative users. ONC guidance supports clear patient identification. They are useful design guidance, not Romanian legal requirements. WCAG targets include at least 4.5:1 normal text and 3:1 large text, visible keyboard focus and no color-only communication. This task is not a full accessibility certification.

The user approved the light default theme and Romanian workbook exception. Other changes are presentation only: clearer English messages, grouping of existing form controls, explicit assumed-record labels and deletion warning, empty states and local font fallback. Original filter defaults, widgets' patient/dose keys, form save transaction and report contract remain. Generated Romanian notes are translated only on display; user-entered notes and names remain intact. No storage or subscription change was implemented.

## Implementation and readiness

The five core modules match the saved pre-redesign SHA-256 baseline. Existing records were not edited for visual testing. All 61 automated tests pass, including new checks that display translation leaves the reporting frame unchanged and that patient text cannot inject HTML. Browser checks use isolated synthetic records; screenshots and limitations are in [verification](VERIFICATION.md).

The app can run locally from source. It is not yet ready for an unrestricted subscription launch: access control, encryption, recovery, auditability, release signing, clinical review and physical-platform testing remain open. See [security](SECURITY_AND_DELIVERY.md) and [delivery plan](DELIVERY_AND_SALES_PLAN.md).
