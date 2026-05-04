# NYC HCFSA Current-State Service Blueprint (Phases 2–5 Context)

## Purpose
Reverse-engineered current-state service blueprint for engineering discovery and implementation planning.

## 1) Employee Enrollment (Annual + Newly Eligible)

### User actions
- Determine eligibility and covered agency status.
- Obtain and complete Enrollment/Change Form.
- Add election amount and eligible dependents.
- Attach required documents and submit through LeapFILE.
- Re-enroll annually during Open Enrollment.

### Staff actions
- Verify eligibility and timing window.
- Check packet completeness and dependent eligibility.
- Enter/update enrollment in FSA records.
- Route out-of-scope institution employees to Benefits Manager.

### Data captured
- Employee identity, agency, benefits eligibility basis.
- Enrollment type, plan year, election amount.
- Dependent roster and eligibility attributes.
- Submission/effective dates and intake status.

### Documents generated
- Enrollment/Change Form record.
- Intake confirmation and exception notices.

### Systems likely involved
- LeapFILE, agency HR/benefits systems, legacy FSA admin tools, email/shared storage.

### Failure points
- Missed enrollment window, incomplete documents, dependency on manual re-keying.

### Opportunities for automation
- Guided enrollment wizard, deadline checks, pre-submit completeness validation, HR data prefill.

## 2) Employee Claim Submission

### User actions
- Prepare HCFSA Claim Form with separate line items.
- Attach required documentation by expense type (EOB, Welfare Fund proof, OTC receipt/box copy when needed).
- Submit packet via LeapFILE (typically once threshold conditions are met).

### Staff actions
- Intake/index packet and check claimant eligibility.
- Validate service date vs plan year/grace period.
- Confirm documentation sufficiency; pend for missing items.

### Data captured
- Claim ID, participant, plan year, expense lines, dates, amounts.
- Channel/timestamps and document metadata.

### Documents generated
- Claim packet record, intake acknowledgment, pending/missing-doc requests.

### Systems likely involved
- LeapFILE, legacy claim adjudication ledger, document repositories, spreadsheet/ticket queues.

### Failure points
- Missing or mismatched documentation, non-eligible service dates, duplicates/partials.

### Opportunities for automation
- Guided claim packet builder, rules-based validation, OCR-assisted extraction, duplicate detection.

## 3) Staff Claim Review (Adjudication)

### User actions
- Respond to requests for additional information if claim is pended.

### Staff actions
- Triage queue and adjudicate using policy rules.
- Compute payable amount against election less fee/prior reimbursements.
- Approve/deny/pend line items with coded reasons and notes.

### Data captured
- Reviewer/timestamps, decision outcomes, reason codes, payable calculations.

### Documents generated
- Decision notices and internal review logs.

### Systems likely involved
- Legacy adjudication platform, manual policy references, operational spreadsheets.

### Failure points
- Inconsistent rule application, manual calculation risk, unclear cutoff operations.

### Opportunities for automation
- Effective-dated rules engine, decision-support UI, SLA-aware queues, immutable audit logs.

## 4) Denial and Appeal Handling

### User actions
- Receive denial letter and submit written appeal within 60 days.
- Provide additional supporting documents as needed.

### Staff actions
- Issue denial with reason.
- Intake/track appeal deadlines.
- Route to Appeals Panel, manage extensions, issue determination.

### Data captured
- Denial reason/date, notice date, appeal receipt date, SLA milestones, final outcome.

### Documents generated
- Denial letter, appeal acknowledgment, extension notice, final determination letter.

### Systems likely involved
- Correspondence templates/PDF tools, email/mail tracking, case logs in legacy tools or spreadsheets.

### Failure points
- Missed deadlines, weak denial rationale, fragmented case history.

### Opportunities for automation
- Deadline calculators + alerts, templated correspondence, unified appeal timeline and SLA dashboard.

## 5) Reimbursement Batch Processing

### User actions
- Track claim status and receive reimbursement payment.

### Staff actions
- Build batch of approved claims.
- Apply configured cutoff policy and reimbursement caps.
- Export to existing payment process and reconcile outcomes.

### Data captured
- Batch ID, included claims, approved amounts, adjustments, transmission/reconciliation status.

### Documents generated
- Batch control reports, payment/export files, reconciliation exception reports.

### Systems likely involved
- Legacy FSA ledger, existing city payment rails, reconciliation spreadsheets.

### Failure points
- 15th vs 25th cutoff ambiguity, export/transmission errors, reconciliation breaks.

### Opportunities for automation
- Configurable batch calendar, automated validations/reconciliation, faster payment status sync.

## 6) Statements and Reporting

### User actions
- Review quarterly statements, monthly payment statements, and annual run-out statement.

### Staff actions
- Generate/distribute required statements.
- Produce operational/tax-supporting reports and legacy-compatible exports.

### Data captured
- Contributions, fees, processed claims, balances, statement dates/status.

### Documents generated
- Quarterly/monthly/annual statements, scheduled/ad hoc reports, PDF/CSV/Excel outputs.

### Systems likely involved
- Legacy reporting modules, spreadsheet reformatting workflows, document distribution tools.

### Failure points
- Cross-system data mismatches, manual output rework, delayed statement production.

### Opportunities for automation
- Standardized reporting model, scheduled generation/distribution, Office-2013-safe templates, report drill-through.

## Cross-Workflow Legacy Tools Likely Involved
- LeapFILE intake channel.
- Legacy FSA administration/adjudication ledger.
- Agency HR/benefits systems for eligibility checks.
- Existing payroll and payment/disbursement systems (retained in first release).
- Shared mailboxes, spreadsheets, and shared-drive document repositories.
