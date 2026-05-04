# NYC HCFSA Current-State Service Blueprint (Phases 2–5 Context)

## Purpose
This document reverse-engineers the likely **current-state** NYC HCFSA workflow from available policy/process constraints to support engineering design for phases 2–5.

---

## 1) Employee Enrollment (Annual + Newly Eligible)

### User actions
- Determine eligibility (NYC health insurance + Citywide contract/Management Benefits Fund + covered agency).
- Obtain Enrollment/Change Form (website, FSA Administrative Office, or agency benefits office).
- Complete form with plan-year election amount and dependent information.
- Attach required eligibility/supporting documentation.
- Submit packet electronically via LeapFILE.
- Re-enroll annually during Open Enrollment (not automatic rollover).

### Staff actions
- Validate employee eligibility and agency coverage.
- Validate enrollment timing (Open Enrollment window or newly eligible within 30 days).
- Verify required documentation completeness.
- Enter/update election and dependents in FSA/benefits records.
- Resolve exceptions (missed window, out-of-scope institutions routed to Benefits Manager).

### Data captured
- Employee identity, agency, employment status.
- Eligibility basis and coverage type.
- Enrollment type (annual/newly eligible/change).
- Election amount and plan year.
- Dependent roster (including adult child age rule validation).
- Submission timestamp and effective date logic.

### Documents generated
- Enrollment/Change Form (submitted artifact).
- Intake confirmation/receipt.
- Exception/routing notices (e.g., institution-specific program referral).

### Systems likely involved
- LeapFILE for intake/transmission.
- Agency HR/benefits systems (eligibility verification).
- Legacy FSA administration system (election/dependent record).
- Email/shared inbox/document storage for manual follow-up.

### Failure points
- Missed 30-day newly eligible window.
- Missing/incorrect dependent listing.
- Incomplete documentation.
- Misclassification of out-of-scope institutions.
- Manual re-keying errors between intake and system of record.

### Opportunities for automation
- Guided enrollment wizard with dynamic eligibility routing.
- Rule-based deadline validation and proactive warnings.
- Auto-completeness checks before submission.
- Structured dependent validation (age/status rules).
- API/file-based prefill from HR master data where available.

---

## 2) Employee Claim Submission

### User actions
- Accumulate claim amount (generally at least $50 unless balance is below $50).
- Complete HCFSA Claim Form; list each expense and claimant separately.
- Gather documentation by expense type:
  - Medical: EOB from insurance carrier.
  - Dental/vision/hearing: Welfare Fund/Union unreimbursed balance documentation.
  - OTC: itemized receipt; if drug name missing, include product box copy.
- Submit claim packet via LeapFILE.

### Staff actions
- Intake and index claim packet.
- Validate claimant eligibility (participant/spouse/dependent/adult child rule).
- Validate service date against plan year/grace period.
- Verify documentation sufficiency per expense type.
- Queue for adjudication or pend for additional information.

### Data captured
- Claim ID, participant ID, plan year.
- Expense lines: claimant, service type, service date, amount.
- Submission date/time, channel, and packet completeness status.
- Document metadata (type, received date, linkage to expense line).

### Documents generated
- Claim Form package.
- Intake acknowledgment.
- Requests for additional documentation (if pending workflow exists).

### Systems likely involved
- LeapFILE intake.
- Legacy claim adjudication/FSA ledger.
- Document repository/network drive.
- Case tracking spreadsheets or ticket queues.

### Failure points
- Missing line-level detail per claimant/expense.
- Incorrect or absent EOB/Welfare Fund documentation.
- OTC documentation mismatch (no identifiable drug name, missing box copy).
- Service date outside eligible period.
- Duplicate/partial submissions with unclear reconciliation.

### Opportunities for automation
- Guided claim packet builder with per-expense document checklist.
- Real-time validation for date windows and claimant eligibility.
- OCR-assisted document extraction + line-item matching.
- Duplicate detection and packet version control.

---

## 3) Staff Claim Review (Adjudication)

### User actions
- Primarily passive; may respond to requests for missing documents.

### Staff actions
- Triage claim queue by submission date and completeness.
- Apply policy rules: eligibility, expense allowability, timing, documentation.
- Compute payable amount against annual election minus fees/prior reimbursements.
- Mark claim/line items approved, denied, or pended.
- Record reason codes and adjudication notes.

### Data captured
- Reviewer identity and timestamps.
- Decision outcomes per claim line.
- Denial/pending reason taxonomy.
- Calculated payable amount and remaining availability.

### Documents generated
- Internal review worksheet/log entries.
- Approval/denial notifications.

### Systems likely involved
- Legacy FSA adjudication platform.
- Manual policy reference guides.
- Spreadsheet-based work queues and QA trackers.

### Failure points
- Inconsistent interpretation of documentation rules.
- Ambiguity around monthly timing cutoffs (15th vs 25th) causing operational variation.
- Manual calculation errors for available reimbursement.
- Limited auditability of reviewer decision rationale.

### Opportunities for automation
- Configurable policy rules engine with effective dating by plan year.
- Standardized decision support UI and denial reason coding.
- SLA-aware work queues and exception flags.
- Full event/audit logging and reviewer analytics.

---

## 4) Denial and Appeal Handling

### User actions
- Receive denial letter with reason.
- Submit written appeal within 60 days of denial notice receipt.
- Provide supplemental evidence/documents if requested.

### Staff actions
- Issue denial letter with specific reason.
- Intake and timestamp appeal.
- Route to Appeals Panel.
- Track 60-day decision SLA; if needed, issue extension notice within 60 days and track up to 60 additional days.
- Record final determination and communicate outcome.

### Data captured
- Denial date, reason, notice delivery date.
- Appeal receipt date and supporting documents.
- SLA milestones: decision due date, extension date, revised due date.
- Final appeal determination and rationale.

### Documents generated
- Denial letter.
- Appeal acknowledgment.
- Extension notice (if applicable).
- Final appeal determination letter.

### Systems likely involved
- Correspondence templates (word processor/PDF generation).
- Email/mail tracking.
- Case log in legacy admin system or spreadsheet.

### Failure points
- Missed appeal deadline tracking.
- Incomplete denial rationale leading to avoidable appeals.
- Manual SLA tracking errors for extension windows.
- Fragmented document history across channels.

### Opportunities for automation
- Rules-based deadline calculator with alerts/escalations.
- Template-driven correspondence generation from reason codes.
- Unified appeal case timeline with immutable audit history.
- Dashboard for panel workload and SLA risk.

---

## 5) Reimbursement Batch Processing

### User actions
- Monitor status and receive payment to employee (not provider).

### Staff actions
- Build monthly reimbursement batch from approved claims.
- Apply timing rules/cutoffs per configured operations policy.
- Validate funding eligibility against annual election cap and prior reimbursements.
- Export payment file/report to existing payment process/system.
- Reconcile batch outcomes and update claim/payment statuses.

### Data captured
- Batch ID, cycle month, included claims.
- Approved amounts, adjustments, offsets/fees.
- Payment transmission status and settlement confirmation.

### Documents generated
- Batch register/control report.
- Payment/export files for downstream disbursement.
- Reconciliation reports and exception lists.

### Systems likely involved
- Legacy FSA ledger/adjudication system.
- Existing city payment/disbursement rails (retained).
- Reconciliation spreadsheets and finance controls.

### Failure points
- Timing-cutoff ambiguity driving inconsistent inclusion logic.
- Reconciliation breaks between approval and payment files.
- Manual export/transmission errors.
- Delayed status updates back to employee-facing channels.

### Opportunities for automation
- Configurable batch policy calendar (15th/25th behavior parameterized).
- Straight-through approved-claim export with validations.
- Automated reconciliation and exception triage.
- Near-real-time payment status synchronization.

---

## 6) Statements and Reporting

### User actions
- Review quarterly statements and monthly claim payment statements (including direct deposit users).
- Use annual statement after run-out for tax/personal records.

### Staff actions
- Generate and distribute quarterly/monthly/annual statements.
- Produce operational and compliance reports.
- Support W-2/HCFSA contribution reporting context.
- Generate legacy-compatible exports (PDF/CSV/Excel Office 2013).

### Data captured
- Monthly contributions, admin fees, processed claims, available balance.
- Statement generation dates and delivery status.
- Run-out closure status and annual finalization flags.

### Documents generated
- Quarterly account statements.
- Monthly claim payment statements.
- Annual statement after run-out.
- Ad hoc and scheduled operational exports/reports.

### Systems likely involved
- Legacy reporting modules.
- Spreadsheet tooling for adjustments/reformatting.
- Document generation/distribution tooling.

### Failure points
- Data mismatches across contribution/claim/payment sources.
- Manual post-processing for Office compatibility.
- Late statement production around run-out close.
- Limited traceability from report totals back to transaction-level records.

### Opportunities for automation
- Standardized reporting data mart/event model.
- Automated scheduled statement generation/distribution.
- Built-in Office 2013-compatible export templates.
- Drill-through audit links from report cells to source transactions.

---

## Cross-Workflow Legacy Tools Likely Involved (Current State)
- LeapFILE for intake/submission of forms and claims.
- Legacy FSA administration/adjudication platform(s) for elections, claims, and balances.
- Agency HR/benefits systems for eligibility verification.
- Existing city payroll and payment/disbursement systems (must remain in place for first release).
- Shared mailboxes, spreadsheets, and network/shared-drive document repositories for case operations and reconciliation.

## Systemic Current-State Pain Points
- Heavy manual indexing/re-keying across disconnected systems.
- Policy execution inconsistencies due to ambiguous or hard-to-trace operational rules.
- Incomplete packet submissions creating preventable denials and rework.
- Fragmented status visibility for employees and staff.
- Limited end-to-end auditability across enrollment, claims, denials, appeals, reimbursement, and reporting.

## Modernization Focus for Phases 2–5 (Within Constraints)
- Add workflow guidance, validation, and configurable policy enforcement layers.
- Preserve existing payroll/payment/legacy FSA integrations rather than replace them.
- Standardize evidence capture, decision traceability, and export/report generation.
- Improve SLA management and operational transparency via shared status and audit timelines.
