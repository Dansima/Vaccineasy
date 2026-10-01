# Security and local-data subscription delivery

Assessment date: 1 October 2026. Launch market confirmed by the user: **Romania**. This is an evidence-based gap assessment, not a compliance certificate or completed penetration test. All architecture changes below await approval.

## What exists today

Patient names, CNPs, phone numbers, birth dates, vaccination records, batches, staff text and notes reside in a local SQLite file. Uploaded files are processed by the local Python server; report bytes are sent to its local browser session and downloaded to the browser's chosen location. The browser receives patient data even though the database is local. Browser downloads, operating-system backups and user-chosen cloud-sync folders can create additional copies outside application control.

The default server is bound to loopback. Compose publishes on host loopback while its container listens on all container interfaces. This does not justify exposing the app to a network. No authentication, database encryption, subscription API, analytics SDK or patient-upload integration was found in the inspected application. Streamlit usage statistics are disabled. The new CSS uses local fonts; the previous external Google Fonts request was removed. This is a source review, not proof of zero network traffic in every environment or dependency.

## Data boundary

| Data | Current location | Proposed hybrid boundary, awaiting approval |
|---|---|---|
| Patient identity / clinical records / import files | Local device and browser session | Remains local; never sent to entitlement service |
| Anexa 1 / CSV downloads | Browser-selected folder | Remains practice-controlled; no automatic upload |
| Backups / encryption keys | No app-managed backup or key system | Encrypted practice-selected local/removable destination; recovery key owned by practice |
| Practice billing identity and subscription | Not implemented | Remote minimal billing account, plan, payment reference, renewal state |
| Device / license check | Not implemented | Random installation ID, signed entitlement, app version; avoid hardware fingerprints and patient counts |
| Network metadata | Local browser/server traffic; installs fetch dependencies | Subscription provider sees IP/time of checks; document retention and processors |
| Diagnostic support | Local logs, no upload flow | Opt-in redacted diagnostics only; no database, raw records or screenshots by default |

Billing metadata is still personal data when it identifies a practitioner. Choose service providers and retention policies explicitly. A local database stored inside OneDrive/iCloud/Dropbox is not a guaranteed local-only arrangement. No cloud storage permission is inferred.

## Feasible delivery models

| Model | Offline use | Updates / backups | Support / cost | Security implications |
|---|---|---|---|---|
| Installed annual subscription with signed offline license | Can operate without periodic online checks; manual renewal/license transfer | Signed downloadable packages; customer-managed local backup | Lowest service footprint; manual renewal and lost-license support | Patient data stays local; vendor holds signing key; token verification and clock/expiry policy needed |
| Installed app + remote subscription management | Local workflows continue within agreed offline allowance | Signed update manifests and packages; local backup service | More infrastructure/support: billing, entitlements, outages, account recovery | Only defined account/license metadata leaves device; entitlement endpoint must never accept clinical payloads |
| Practice-local server + subscribed client access | Can work within practice LAN when internet is down | Central practice-controlled backup/update | More expensive installation/network administration | Records remain on practice server but reach authorized LAN devices; requires HTTPS, roles and concurrency testing |

A conventional hosted Streamlit SaaS executes on the vendor's server, where SQLite and imports would reside. It does not satisfy the requested local-data boundary. Browser-only encrypted local storage would require a substantial rewrite and different threat model; it is not recommended for this iteration.

**Recommendation:** retain Streamlit/SQLAlchemy/SQLite for a single-workstation pilot. Select signed annual offline licensing for a simple first commercial release, or hybrid entitlements if automatic billing and renewal are essential. The latter remains an installed subscription product with a remote control service, not hosted patient-data SaaS. Do not switch to PostgreSQL solely for subscriptions.

**Decisions:** offline license versus hybrid; number of seats/devices; entitlement refresh/grace; expiry behavior; recovery ownership. Suggested hybrid policy for discussion: cache a signed entitlement for 30 days, show clear renewal status, retain read/export access after expiry and never delete or encrypt records as a payment penalty. Write restrictions and downtime behavior require approval and clinician testing.

## Prioritized gaps and mitigations

| Priority | Evidence / threat | Recommended control and verification | Dependency |
|---|---|---|---|
| High | Any person with local/browser access can read or change records | Local accounts, roles, secure password hashes, idle lock, recovery; test unauthorized and expired sessions | Approved authentication workflow |
| High | Plain SQLite and exports expose CNP/health data if device stolen | OS full-disk encryption as immediate practice measure; evaluate SQLCipher/local encryption and encrypted backups; test platform/driver and locked-device cases | Key/recovery decision |
| High | No key management | OS credential vault for device secrets; separately stored practice recovery material; no hardcoded keys or password-only universal key; no vendor escrow without explicit decision | Encryption choice |
| High | Unchecking destroys records; history not immutable | Actor/timestamp/reason audit with retained corrections; restrict log access and retention; test recovery and integrity | Authentication and schema approval |
| High | No automated recovery or versioned migrations | Consistent SQLite backup API or stopped-app backup, encrypted rotation, checksums and separate restore drill; migrations with pre-update backup/rollback | Approved backup/schema design |
| High | Source packages/dependencies not locked or signed | Lock tested versions, dependency scans/SBOM, release signing/notarization, rollback packages, least-privilege runtime | Packaging and supported OS decision |
| High | Exception/debug paths and ORM repr can expose identifiers | Review logging and tracebacks; redaction tests with synthetic canaries; no analytics or raw diagnostic upload; prevent credentials in logs | Logging policy |
| High | Boundary inferred from code only | Verify listening sockets, runtime requests, backup destinations, Docker volume permissions and network-disabled operation | Release acceptance testing |
| Medium | Files can be corrupted/oversized; CSV downloads carry sensitive data | File/import limits and storage error recovery review; minimal exported data; secure disposal guidance | Any limit/default changes need approval |
| Medium | Shared LAN access not protected | Keep loopback default; authorize network deployment separately with TLS, firewall, roles and capacity tests | Separate local-server scope decision |

SQLite transactions and unique constraints help integrity but do not replace access control, audit or backups. Encryption protects data at rest, not a compromised unlocked session. Application audit logs are themselves sensitive and must remain local and access-controlled. Avoid opening the port publicly or enabling remote support that can view patient records without a specific approved support arrangement.

For the proposed backup implementation, [SQLite's official online backup API](https://www.sqlite.org/backup.html) offers a consistent snapshot without relying on copying a changing database file. [SQLCipher's vendor documentation](https://www.zetetic.net/sqlcipher/) describes database encryption and multiple distribution editions; Python-driver compatibility, redistribution licensing, performance and recovery must be evaluated before selecting it. These are candidate implementation choices, not installed controls.

## Romania / EU requirements to assess

**Verified legal framework:** GDPR treats health information as special-category data. A lawful basis under Article 6 and an applicable Article 9 condition need to be established; local storage does not remove the obligations. Articles 25/32 concern privacy by design and appropriate security; Article 28 is relevant if the vendor becomes a processor through support or services. Article 35 requires a DPIA where the risk threshold is met. Article 33 includes the applicable 72-hour supervisory notification rule, with its conditions. These are a starting checklist, not a determination for this product. [GDPR official text](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32016R0679).

Romania's [ANSPDCP Decision 174/2018](https://www.dataprotection.ro/servlet/ViewDocument?id=1556) lists processing requiring DPIA. Assess scale, vulnerable children and health-data criteria with a qualified adviser; do not assume either every individual practice needs a DPIA or none does. Review [Law 190/2018](https://ans-extmail.dataprotection.ro/index.jsp?lang=ro&page=Legea_nr_190_2018) for applicable national provisions, including identifier handling. This review has not established a product-specific legal basis, retention period, DPO obligation or CNP policy.

Scheduling/status functionality requires an intended-purpose assessment before sales claims. Software qualification depends on actual intended medical purpose, not just the use of Streamlit or a disclaimer. Review [MDCG 2019-11 rev.1, June 2025](https://health.ec.europa.eu/latest-updates/update-mdcg-2019-11-rev1-qualification-and-classification-software-regulation-eu-2017745-and-2025-06-17_en) with a regulatory specialist. No conclusion that Vaccineasy is or is not a medical device has been established.

**Required decisions and evidence before launch:** controller/processor roles, clinical and intended-purpose scope, lawful basis and notices, retention/deletion policy, DPIA screening, support access model and contracts, incident-response owner, independent security review and documented restoration. No GDPR, MDR, WCAG or official-report compliance claim is made.
