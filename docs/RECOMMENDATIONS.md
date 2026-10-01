# Decisions before further implementation

Only English presentation, the approved light theme, documentation and backlog organization were implemented. The items below change functionality, defaults or architecture and **await the user's approval**. Priority is relative to a practice-ready launch; estimates are preliminary developer days, excluding external review.

| Priority | Recommendation / decision | Benefit | Tradeoff / behavior change | Estimate |
|---|---|---|---|---|
| High | Replace import assumptions with Unknown / Documented / Administered provenance after clinical review | Prevents assumed doses appearing equivalent to verified care | Changes statuses/reports and needs migration/reconciliation; current rules retained | 4–7 |
| High | Review vaccine/calendar coverage and report acceptance with Romanian practitioners | Establishes intended scope and exact clinical meaning | Independent pneumococcal/birth doses or calendar versions change data and calculations | 3–6 for assessment; implementation scoped afterward |
| High | Replace destructive unchecking with reviewed corrections and an audit trail | Recoverable changes and accountable history | New save/correction workflow, actor identity, retention and schema | 4–6 |
| High | Select local subscription model and offline entitlement policy | Commercial delivery without patient cloud storage | Remote account metadata for hybrid model; signed renewal operations for offline model | 3–5 architecture; 5–8 implementation |
| High | Local authentication, roles and idle lock | Restricts shared-workstation access | Sign-in step, recovery and user administration | 3–5 |
| High | Encryption and recoverable key handling | Reduces lost-device/backup exposure | Key loss risk, driver/platform testing, migration and recovery ownership | 4–7 |
| High | Automated encrypted local backups with tested restoration | Reduces data-loss risk | Storage management, retention policy, extra key handling | 3–5 |
| Medium | Shared patient selection or direct overview-to-record navigation | Fewer patient-selection repetitions | Changes cross-tab state and navigation; wrong-patient safeguards needed | 2–3 |
| Medium | Search/filter/export enhancements after pilot evidence | Faster high-volume work | Adds scope/options; current native searchable selectors/table tools retained | Scope after evidence |

Choose delivery model first; authentication, correction/audit, encryption and backups need an agreed design before implementation. Clinical provenance and calendar changes require independent decisions and evidence. Usability sessions can measure the current interface before approving navigation additions. No reminder, messaging, RENV integration or hosted patient database is assumed in the scope.
