# Delivery and sales plan — Romania

Prepared 1 October 2026. **Facts** are repository findings or attributed public vendor statements. **Recommendations** describe future work. All prices, effort, conversion and cost figures below are **planning hypotheses**, not quotes or established demand. No outreach, sales publication or billing service has been initiated.

## Product overview and target buyer

Confirmed product: a local pediatric vaccination register with ICMED file import, age-based status review, administration recording, historical date views and paginated Romanian Anexa 1 export. English interface; Romanian official workbook. Proposed positioning: **“Prepare your vaccination list and monthly register from existing patient exports, with patient records kept on your practice computer.”** Do not claim live ICMED/RENV synchronization, a full national-calendar clinical engine, certified compliance, independent pneumococcal evidence or prevention of missed vaccinations.

Primary target hypothesis: Romanian independent family practices with pediatric lists, existing ICMED exports and recurring monthly register preparation. Buyer: practice owner GP; daily operator: GP and practice nurse. Initial target is a single workstation. Multi-seat/server use requires a separately approved access-control deployment.

Validate these needs through 8–12 interviews: time spent assembling monthly lists, confidence in inherited vaccination history, manual copying, import compatibility, offline preference, backup ownership and willingness to use an English interface. Do not assume English is acceptable to all Romanian operators; optional Romanian UI localization would be a new decision. Record process metrics and anonymous themes, not patient files.

## Competitors and differentiation

| Alternative | Verified public positioning | Differentiation hypothesis / next evidence |
|---|---|---|
| [icMED cabinet software](https://www.icmed.ro/cabinete.html) | Vendor markets online family-practice software within a broader modular ecosystem | Complement existing exports rather than replace the practice system; demo exact report workflow and ask about current alternatives |
| [DOCS Medicina de Familie](https://www.softmedical.ro/medicina-de-familie) | Vendor publishes GP product releases covering broad practice documentation/reporting functionality | Focused onboarding and a narrow vaccination workspace; compare live report effort, not a claim that competitors lack vaccination tools |
| [Easy Medical Pro](https://demo.easymedical.ro/presentation.asp?appid=1&pageMenuID=3) | Vendor presentation describes appointments, reception, laboratory and administrative modules | Adjacent broader clinic system; published presentation appears legacy and needs live capability verification |
| Excel / paper | Status-quo hypothesis to verify in interviews, not a measured market share | Reusable age/date calculations and consistent workbook pagination; quantify actual time/error differences |

Research did not establish comparable current published prices, offline guarantees or full competitor vaccination behavior. Request demos/quotes as a later sales-research task; do not invent pricing gaps. Differentiation must be demonstrated through reliable imports, transparent assumptions, preserved reporting, local recovery and fast daily tasks. Current security controls are insufficient to market “secure by design” as a proven attribute.

## Pilot and measurable acceptance

Recommendation: recruit 5–8 GPs, including nurses where applicable, for a 6–8-week controlled pilot after privacy, clinical and security gates. Use synthetic records for discovery and training. Any real-data pilot needs a practice-controlled installation, agreed roles, backup/restore, clear assumptions and approved handling arrangements. No copies of patient databases should be collected centrally.

1. Baseline: time two representative monthly list/report tasks and record current data-reconciliation effort.
2. Observe five tasks: import a valid file, interpret rejected rows, find a patient, record/inspect a dose and export a historical month. Include wrong-patient-switch and assumed-record scenarios.
3. Measure unassisted completion, median elapsed time, errors/near misses, assistance requests and recovery success. Record measurements locally; transfer only agreed anonymous aggregates.
4. Review workbook reconciliation with each practice and a clinical reviewer; check every sampled vaccine column and date interpretation against their approved process.
5. Obtain structured usability feedback and willingness-to-pay evidence, then decide changes before implementing them.

Proposed success gates: at least 90% core tasks unassisted; at least 30% median reduction in monthly preparation time against paired baseline; zero wrong-patient writes or silent data loss; 100% reconciliation of sampled workbook entries; successful separate-copy restore at every pilot practice; at least four of six completing practices willing to pay the tested price. These are proposed thresholds, not results. Pause real-data pilot use for a critical safety/privacy defect and investigate before resumption.

## Product readiness, installation and support

Before release: clinician-signed scope/assumptions, report acceptance evidence, approved provenance policy, authentication/recovery, encryption/backup design, tested restores, local audit/corrections, offline operation, signed packages, locked dependencies and schema rollback. Retain SQLite for single-device use; no unnecessary frontend/backend rewrite.

Package candidates after architecture approval: signed Windows installer and signed/notarized macOS Apple Silicon package with a bundled tested Python runtime, self-contained local launcher, per-user data path, uninstall that retains data, version/about page and rollback installer. Linux/Docker can remain a documented technical option. Do not ship a Windows virtual environment to a Mac. Specify supported OS versions only after testing on physical machines; test install/update/uninstall with standard-user accounts and low disk space. Include dependency/license notices and SBOM. Certificate/notarization procurement and packaging licenses require separate actual quotes.

Onboarding: 20-minute synthetic walkthrough, confirm storage/backup location, test import on a protected copy, reconcile counts, explain assumptions and deletion behavior, run a restore drill, then obtain practice acceptance. Supply the English README, one-page workflow card, backup guide and support/privacy terms. This task supplies the README and plans; installers and formal contracts remain future deliverables.

Support proposal: business-hours email/ticket channel; initial target response one business day, not a contracted SLA yet. Critical data/safety incidents route to a named engineering/clinical owner. Default to version/error codes and synthetic reproduction, not database uploads. Screen sharing or record access requires a specific support agreement and session authorization. Offer monthly office hours during pilot and a quarterly restore reminder only after an approved product/support design. Maintain release notes, incident runbook and a known-limits page.

## Pricing and subscription hypotheses

| Offer to test | Proposed price | Scope / assumptions |
|---|---|---|
| Single-practice pilot | Free limited 6–8-week evaluation | Named cohort, explicit pilot terms, no automatic recurring charge |
| Local Essential | RON 79/month or RON 790/year | One workstation; updates and standard support after approved security release |
| Local Assisted | RON 129/month or RON 1,290/year | Same clinical features, additional onboarding/priority assistance with a defined cap |
| Optional installation assistance | RON 250–500 one time | Depends on workstation/backup complexity; no unlimited remote clinical-data access |

Prices exclude VAT where applicable and payment fees; legal/tax adviser must confirm invoice/tax treatment. No subscription or payment collection exists today. Do not sell multi-user rights until the architecture supports them. Test prices with direct willingness-to-pay interviews and paid commitments after pilot; do not use hypothetical survey approval alone.

Planning unit economics: 100 Essential annual customers at RON 790 produce RON 79,000/year before VAT/tax/refunds. Hypothetical 3% payment fees, RON 6,000/year service infrastructure and 15 minutes/month support per practice at RON 120/hour consume about RON 44,370/year, leaving RON 34,630 before development, security review, sales and overhead. Assisted support needs its own cap and model. Validate support burden; a small customer base may not finance the initial build. Do not infer guaranteed profitability.

## Acquisition and sales materials

Start with founder-led demonstrations and pilot referrals through GP professional groups and local practice networks, with permission from organizers. Approach practice-software consultants and relevant training events for a complementary-workflow demonstration. Avoid paid advertising until retention and price are tested. No messages were sent as part of this task.

Prepare: a one-page English product sheet, a 90-second synthetic demo, transparent local-data/security sheet, sample Romanian workbook with synthetic identities, competitor comparison based on verified demos and a short landing-page draft. Publish only after separate approval. Avoid screenshots of real patients, promises of medical outcomes and unsupported integration claims.

Demo script: import four synthetic patients; explain one-time assumptions; show due/overdue/upcoming labels; select a patient and check name/CNP; record an eligible dose; review historical date effects; generate Anexa 1; show where local backup lives. Close with the practice's current time cost, operator language preference and trial acceptance criteria. Qualification questions: export availability, monthly workload, operator count, device policy, recovery arrangements and purchase authority.

Track an initial hypothetical funnel: 30 qualified conversations → 12 demos → 6 pilot practices → 4 paying practices. Measure actual demo-to-pilot, pilot-to-paid, monthly active report generation using voluntary aggregate feedback, support minutes, cancellations and recovery failures. No covert product telemetry is proposed.

## Milestones, dependencies and budget

| Gate / milestone | Calendar window hypothesis | Effort | Depends on / exit evidence |
|---|---|---|---|
| M0: UI and assessment | Current task | Completed presentation/research | 61 tests, core hashes, synthetic browser checks; review docs |
| M1: discovery and decisions | Weeks 1–2 | 3–5 developer days + clinician/adviser time | 8–12 interviews; model/provenance/security scope approved |
| M2: safety/security foundations | Weeks 3–6 | 15–24 developer days | Auth, keys, backups, corrections/audit and migration design approved; recovery/security checks pass |
| M3: packaging and release testing | Weeks 6–8 | 8–12 developer days | Physical Windows/Apple Silicon machines, signing accounts; update/uninstall/rollback/network tests |
| M4: controlled pilot | Weeks 9–16 | 4–9 developer days of observation/support | Clinical/privacy readiness; measurable pilot gates; fixes budgeted separately |
| M5: limited paid release | Week 17+ | Operational work | Accepted evidence, contracts/prices/support owner, no critical defects |

Total initial engineering planning range: **30–50 days at an assumed RON 1,200/day = RON 36,000–60,000**. Add external legal/regulatory/security review **RON 8,000–15,000**, discovery/demo/testing expenses **RON 3,000–6,000**; then 20% contingency gives **RON 56,400–97,200** before taxes and recurring operations. These are budget allowances, not supplier quotes. Independent clinical scope expansion, regulated-device obligations or multi-seat deployment can substantially exceed them. Component estimates in recommendations are alternatives, not all automatically included in this budget; re-estimate after decisions.

Dependencies: clinician reviewer, Romanian privacy/regulatory adviser, release/security engineer, Apple Silicon and Windows test hardware, signing accounts, support owner, chosen entitlement/payment providers and written data-handling policies. No external procurement has been made.

## Risks and launch criteria

| Risk | Mitigation / owner needed |
|---|---|
| Assumed history mistaken for actual vaccination | Clinical/provenance decision, explicit training, reconcile historical evidence; clinical owner |
| Workbook rejected or scope mismatched | Practice/administrative review and sampled reconciliation; clinical/product owner |
| Lost device/key or failed restore | Encryption/recovery design and actual restore evidence; security/support owner |
| Bad update corrupts schema | Signed tested packages, stopped/consistent backups and rollback; release owner |
| Subscription outage blocks care | Explicit offline/expiry policy tested with practitioners; product owner |
| Low willingness to pay / English adoption | Interviews and paired time savings, price experiment; commercial owner |
| Incumbent offers equivalent workflow | Direct comparison and complementary positioning; commercial owner |
| Regulatory intended-purpose obligations | Specialist assessment before claims and real-data launch; legal/regulatory owner |

Paid launch requires every high-priority safety/security decision resolved, no critical open defect, approved clinical/reporting scope, verified restore/update path, platform test matrix, privacy/support documents, agreed offline entitlements, pilot targets met or explicitly revised with evidence, and accountable launch sign-off. The current app is suitable for source-based demonstration and controlled evaluation, not a claim of completed commercial readiness.
