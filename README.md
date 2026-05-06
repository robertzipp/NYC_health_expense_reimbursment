# NYC HCFSA Reimbursement Workflow — Engineering Product Brief (Phases 2–5)


## Target Implementation Stack
- **Frontend:** React with TypeScript for employee and staff web workflows.
- **Backend:** .NET / ASP.NET Core Web API for REST endpoints, orchestration, validation, authorization boundaries, and audit-event creation.
- **Database:** Microsoft SQL Server with reviewed T-SQL migrations and SQL Server-native types for durable workflow, policy, and audit records.
- **Current repository baseline:** Existing Python/SQLite code remains a prototype/reference implementation until the React/.NET/T-SQL stack reaches feature parity for the first vertical slice.
- **First vertical slice constraint:** Implement only draft claim creation, one expense, document metadata attachment, validation, submission, and audit events; exclude payment processing, payroll integration, binary file storage, and legacy-system replacement.

## Scope
This brief covers:
1. Guided claim packet builder
2. Enrollment and re-enrollment wizard
3. Status tracking, denial repair, and appeals
4. Back-office modernization

## Goals
- Reduce preventable claim denials by guiding employees to submit complete, policy-compliant claim packets.
- Improve enrollment completion and annual re-enrollment completion through step-by-step eligibility and deadline guidance.
- Provide transparent end-to-end status visibility from submission through reimbursement/denial/appeal outcomes.
- Enable staff to process claims, denials, and appeals faster with configurable policy rules and better operational tooling.
- Preserve policy fidelity across plan years via configurable limits, fees, deadlines, documentation rules, and recipient eligibility logic.
- Produce legacy-compatible outputs (PDF/CSV/Excel for Office 2013) and complete audit trails.

## Non-Goals (First Release)
- Replacing payroll systems.
- Replacing payment/disbursement systems.
- Replacing all legacy FSA systems end to end.
- Redefining policy where source material is ambiguous (e.g., 15th vs 25th monthly cutoff behavior).
- Policy expansion beyond provided HCFSA rules.

## Primary Users
- NYC employees filing enrollment, re-enrollment, and reimbursement claims.
- Employee dependents/spouses as expense recipients (indirectly represented in employee workflows).
- Agency benefits administrators and FSA administrative office reviewers.
- Appeals panel and operations staff managing denials, appeals, and audit/reporting.

## Constraints
- Must enforce current eligibility, enrollment windows, documentation requirements, and timing rules as configurable policy.
- Must route potentially out-of-scope organizations (e.g., cultural institutions/libraries/DOE charter schools) to Benefits Manager guidance.
- Must support LeapFILE-based intake/submission in current-state operations.
- Must distinguish and persist: expense date, claim submission date, plan year, grace period dates, and run-out deadline.
- Must support reimbursement eligibility up to annual election minus fees/prior reimbursements regardless of current account balance.
- Must maintain immutable audit trail for enrollment actions, submissions, uploads, reviews, denials, appeals, exports, and reimbursement state changes.
- Must support exports/statements required by operations and tax reporting context.

## Assumptions
- Policy values are administered through configuration by plan year (e.g., min/max contribution and admin fee).
- 2025 limits: min $260, max $3,300; 2026 limits: min $260, max $3,400; lower maximums may apply for some employees.
- Administrative fee may be configured up to $48/year or $4/month.
- Open enrollment generally occurs September–November; newly eligible enrollment window is 30 days from health-benefit eligibility.
- Claims and forms continue to flow through existing channels (including LeapFILE) in this release.
- The 15th deposit cutoff vs 25th processing cutoff conflict remains an open policy/operations decision and must be parameterized, not hard-coded.

## Success Metrics
### Employee Experience
- Claim packet completion rate (started vs submitted).
- First-pass claim approval rate (no additional documentation requested).
- Re-enrollment completion rate during annual open enrollment.
- Time to submit complete claim packet (median).

### Operations
- Manual touch rate per claim (reviews/rework actions per claim).
- Denial rate attributable to missing/invalid documentation.
- Appeal cycle time (denial notice to appeal determination).
- Back-office throughput (claims processed per reviewer per month).

### Compliance & Reliability
- Percentage of transactions with complete audit events.
- Policy configuration change lead time (request to production activation).
- Export success rate for PDF/CSV/Excel (Office 2013 compatible) and statement generation timeliness.
- Zero critical defects involving plan-year/grace-period/run-out date classification.

## Delivery Notes for Engineering
- Implement policy engine/config model first; all workflows should consume shared policy configuration.
- Separate orchestration from system-of-record integrations so legacy payroll/payment/FSA dependencies remain intact.
- Treat ambiguous operational rules as feature-flagged/configurable with explicit operational ownership.
- Prioritize observability: event logs, reviewer action history, denial reason taxonomy, and appeal SLA tracking.
