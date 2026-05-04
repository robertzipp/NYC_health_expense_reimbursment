# NYC HCFSA Target-State User Journeys

## Purpose
This document defines target-state user journeys for the HCFSA platform to guide implementation, QA, and operations readiness for phases 2–5.

---

## 1) Employee Saves a Receipt Before Reaching the Claim Submission Threshold

**Trigger**
- Employee incurs an eligible expense but has not yet reached the claim submission threshold.

**Actor**
- Employee.

**Preconditions**
- Employee has an active HCFSA enrollment for the relevant plan year.
- Employee can access authenticated claim workspace.
- Expense date is within plan year or grace period.

**Main path**
1. Employee opens “Save Expense/Receipt” flow.
2. Employee enters expense basics (recipient, service date, category, amount, provider/merchant).
3. Employee uploads receipt image/PDF.
4. System validates minimum metadata and stores as draft expense.
5. System computes running draft total and shows threshold progress.
6. System confirms receipt saved and claim not yet submitted.

**Alternate paths**
- Employee chooses to submit immediately if exception condition applies (e.g., account balance below threshold policy).
- Employee adds multiple receipts in one session.

**Error states**
- Unsupported file type/size.
- Missing mandatory fields.
- Expense date outside allowable window.
- Duplicate receipt detected.

**Required data**
- Employee ID, plan year, recipient type/name.
- Expense date, category, amount, merchant/provider.
- Receipt file, upload timestamp, draft status.

**Notifications**
- In-app confirmation of saved draft.
- Optional email: “Receipt saved, ready when threshold reached.”

**Acceptance criteria**
- Draft expense persists without creating a submitted claim.
- Threshold progress reflects all draft expenses.
- Audit log records create/update/upload actions.

---

## 2) Employee Submits a Claim With Multiple Expenses

**Trigger**
- Employee chooses to submit a claim containing 2+ expense line items.

**Actor**
- Employee.

**Preconditions**
- Employee authenticated with active plan-year enrollment.
- At least one expense line exists in draft.
- Required per-line documentation is available.

**Main path**
1. Employee opens claim builder and selects multiple draft expenses (or creates new lines).
2. Employee verifies each line’s claimant, date of service, service type, and amount.
3. System enforces line-level documentation checklist by expense type.
4. Employee submits claim packet.
5. System assigns claim ID and line IDs; status set to “Submitted.”
6. System displays tracking timeline and expected next step.

**Alternate paths**
- Employee removes a line that fails validation and submits remaining lines.
- Employee saves as draft and submits later.

**Error states**
- Missing documentation on one or more lines.
- Ineligible claimant or service date.
- Total/line amount parse failure from malformed entry.

**Required data**
- Claim ID, participant ID, plan year.
- Per-line: claimant, service date, category, amount, document links.
- Submission timestamp, channel, status.

**Notifications**
- Submission confirmation with claim ID.
- In-app status entry created in timeline.

**Acceptance criteria**
- Each expense is stored as a distinct adjudicable line item.
- Submission blocked until required docs exist per line.
- Timeline and audit trail are immediately visible to employee and staff.

---

## 3) Employee Submits an OTC Claim With Incomplete Receipt Detail

**Trigger**
- Employee submits OTC expense where receipt does not clearly identify product/drug.

**Actor**
- Employee.

**Preconditions**
- Employee has OTC expense line in claim builder.
- OTC documentation rules are configured for plan year.

**Main path**
1. Employee selects OTC category and uploads itemized receipt.
2. System checks receipt metadata/OCR for identifiable drug name.
3. If name not found, system prompts for product box image upload.
4. Employee uploads product box image and completes submission.
5. System marks OTC line as documentation-complete and submits claim.

**Alternate paths**
- Receipt already contains drug name; no box upload required.
- Employee saves as draft and returns later with box image.

**Error states**
- Employee attempts submit without required box image after OTC check fails.
- Uploaded supplemental image unreadable/corrupt.

**Required data**
- OTC line item details, receipt file, product box file (conditional), validation result.

**Notifications**
- Real-time UI prompt for missing OTC evidence.
- Submission confirmation or blocking message with remediation guidance.

**Acceptance criteria**
- OTC rule enforcement is conditional and policy-driven.
- Submission is blocked only when required supplemental evidence is missing.
- Denial-preventive guidance is shown before final submission.

---

## 4) Employee Re-Enrolls for a New Plan Year

**Trigger**
- Open Enrollment period begins for upcoming plan year.

**Actor**
- Employee.

**Preconditions**
- Employee meets eligibility requirements.
- Enrollment window is open.
- Plan-year contribution limits/fees configured.

**Main path**
1. Employee receives Open Enrollment prompt.
2. Employee opens re-enrollment wizard with prior-year data prefilled where permissible.
3. Employee confirms eligibility and updates dependents.
4. Employee selects annual election within configured min/max.
5. Employee reviews attestations and submits.
6. System records election for next plan year and returns confirmation.

**Alternate paths**
- Employee changes agency/eligibility context and is routed for manual review.
- Employee exits and resumes draft before deadline.

**Error states**
- Election amount outside allowed range.
- Missing required dependent information.
- Submission attempt after enrollment window closes.

**Required data**
- Employee eligibility status, plan year, election amount, dependent roster, attestation timestamps.

**Notifications**
- Open Enrollment reminder(s).
- Submission confirmation with effective date expectation.
- Deadline warning reminders for incomplete drafts.

**Acceptance criteria**
- Re-enrollment is not automatic and requires explicit annual submission.
- Election validation uses plan-year-configured thresholds.
- Confirmation includes plan year and submitted election amount.

---

## 5) Reviewer Requests Missing Documentation

**Trigger**
- Reviewer finds claim line(s) lacking required evidence.

**Actor**
- Reviewer (staff).

**Preconditions**
- Claim is in “Submitted” or “Under Review.”
- Missing-doc reason codes configured.

**Main path**
1. Reviewer opens claim and flags deficient line(s).
2. Reviewer selects standardized missing-document reason(s).
3. Reviewer sets response due date per policy/operations configuration.
4. System transitions claim status to “Pending Employee Action.”
5. System sends structured request to employee with exact missing items.

**Alternate paths**
- Reviewer requests docs for only subset of lines while other lines continue review.
- Reviewer adds custom note in addition to standardized reasons.

**Error states**
- Reviewer attempts pending action without selecting reason code.
- Due date outside configured bounds.

**Required data**
- Claim/line IDs, reason codes, reviewer notes, due date, status transition timestamp.

**Notifications**
- Employee alert (email + in-app): missing documentation request.
- Reviewer queue update showing pending response SLA.

**Acceptance criteria**
- Missing-document requests are line-specific and reason-coded.
- Status transition and due date are auditable.
- Employee receives actionable checklist, not generic message.

---

## 6) Employee Repairs a Claim After Missing Documentation Is Requested

**Trigger**
- Employee receives “Pending Employee Action” request.

**Actor**
- Employee.

**Preconditions**
- Claim has open documentation request.
- Employee can access requested line-item checklist.

**Main path**
1. Employee opens claim timeline and views missing items.
2. Employee uploads required documents per flagged line.
3. Employee adds optional explanatory notes.
4. Employee resubmits for review.
5. System marks request satisfied and returns claim to reviewer queue.

**Alternate paths**
- Employee partially fulfills request and saves draft response.
- Employee replaces previously uploaded incorrect document.

**Error states**
- Resubmit attempt with unresolved required items.
- Expired response window (if operational policy imposes closure).

**Required data**
- Request ID, required-item checklist, uploaded files, employee notes, resubmission timestamp.

**Notifications**
- Employee confirmation of successful resubmission.
- Reviewer notification: claim ready for re-review.

**Acceptance criteria**
- System prevents resubmission until required items are complete.
- Prior and replacement documents remain in audit history.
- Claim re-enters review without new claim creation.

---

## 7) Reviewer Denies a Claim

**Trigger**
- Reviewer determines claim/line is not reimbursable after review.

**Actor**
- Reviewer (staff).

**Preconditions**
- Claim has completed review evidence.
- Denial reason taxonomy and letter templates are configured.

**Main path**
1. Reviewer selects denied line(s) and denial reason code(s).
2. Reviewer adds required rationale text.
3. System generates denial notice content from template + reason codes.
4. Reviewer confirms and issues denial.
5. System updates status to “Denied” and starts appeal window clock.

**Alternate paths**
- Partial denial: some lines denied, others approved.
- Supervisor review required before final denial issuance.

**Error states**
- Denial attempt without required reason/rationale.
- Template generation failure.

**Required data**
- Denial reason codes, rationale text, notice issue date, affected line IDs, appeal deadline date.

**Notifications**
- Employee denial notice with reason and appeal instructions.
- Internal audit event and queue update.

**Acceptance criteria**
- Every denial has structured reason code and human-readable rationale.
- Appeal deadline is calculated and displayed.
- Denial notice is reproducible from stored record.

---

## 8) Employee Submits an Appeal

**Trigger**
- Employee disagrees with denial and files appeal.

**Actor**
- Employee.

**Preconditions**
- Claim denial exists.
- Appeal submitted within allowable timeframe (60 days from denial notice receipt).

**Main path**
1. Employee opens denied claim and starts appeal form.
2. Employee provides written appeal statement and uploads supporting evidence.
3. System validates deadline and completeness.
4. Employee submits appeal.
5. System creates appeal case, status “Under Appeal Review,” and assigns SLA milestones.

**Alternate paths**
- Employee starts draft appeal and submits later (before deadline).
- Employee withdraws draft prior to submission.

**Error states**
- Appeal submitted after deadline.
- Missing required written statement.
- Unsupported evidence file format.

**Required data**
- Appeal case ID, linked denial/claim IDs, statement text, document set, receipt timestamp, SLA due dates.

**Notifications**
- Appeal submission acknowledgment.
- Appeals staff queue alert with due-by date.

**Acceptance criteria**
- Late appeals are rejected with clear reason.
- On-time appeals get case ID and SLA tracking immediately.
- Appeal record is fully linked to original denial and claim.

---

## 9) Admin Generates a Reimbursement Batch

**Trigger**
- Scheduled batch cycle date arrives for reimbursement processing.

**Actor**
- Admin/operations staff.

**Preconditions**
- Approved claim lines exist and are not yet paid.
- Batch cutoff/timing rules configured (including unresolved 15th vs 25th logic as configurable parameter).

**Main path**
1. Admin initiates “Generate Batch” for cycle.
2. System selects eligible approved claims by configured criteria.
3. System runs preflight checks (duplicates, cap validations, missing payment profile exceptions).
4. Admin reviews batch summary and confirms.
5. System creates immutable batch record and export artifacts for downstream payment system.
6. Batch status transitions to “Transmitted” then “Reconciled” as confirmations return.

**Alternate paths**
- Admin excludes specific exception claims before finalization.
- Dry-run mode used for preview without committing batch.

**Error states**
- No eligible claims found.
- Preflight validation failures block batch creation.
- Downstream transmission/reconciliation failure.

**Required data**
- Batch ID, cycle period, included claim IDs/amounts, exclusions, validation results, transmission metadata.

**Notifications**
- Internal success/failure alerts for batch generation and transmission.
- Exception report notifications to operations queue.

**Acceptance criteria**
- Batch creation is deterministic from configured rules.
- All inclusions/exclusions are traceable and auditable.
- Export artifacts are compatible with retained downstream process.

---

## 10) Admin Exports an Excel-Compatible Operational Report

**Trigger**
- Admin requests operational report for monitoring, reconciliation, or audit.

**Actor**
- Admin/operations/reporting staff.

**Preconditions**
- Report template exists.
- User has permission to export operational data.

**Main path**
1. Admin chooses report type, date range, filters, and output format.
2. System validates parameters and starts report job.
3. System generates report in Office 2013-compatible Excel format.
4. Admin downloads file and optional companion CSV/PDF.
5. System logs export event with user, filters, and timestamp.

**Alternate paths**
- Scheduled recurring export delivered to secure distribution channel.
- Large report generated asynchronously with completion notification.

**Error states**
- Invalid filter combination or oversized synchronous request.
- Export format conversion failure.
- Permission denial.

**Required data**
- Report definition ID, filter set, execution timestamp, requesting user ID, output file metadata.

**Notifications**
- In-app export completion message.
- Optional email with secure link/availability notice.
- Failure notification with retry guidance.

**Acceptance criteria**
- Excel output opens successfully in Office 2013.
- Export contains correct filtered dataset and totals.
- Export action is fully auditable.
