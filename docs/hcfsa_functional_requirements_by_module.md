# NYC HCFSA Functional Requirements by Module

## Purpose
This document converts the target-state user journeys into implementation-ready functional requirements organized by product module.

## Priority Legend
- **Must**: required for MVP/compliance-critical behavior.
- **Should**: high-value behavior expected in standard operations.
- **Could**: optional enhancement; implement when capacity allows.

---

## 1) Claim Builder

### FR-CB-001
- **Description:** The system shall allow an employee to create and maintain a multi-line claim draft with line-level fields: claimant, service date, category, amount, provider/merchant, and notes.
- **Priority:** Must
- **Actor:** Employee
- **Inputs:** Employee ID, plan year, line item form fields.
- **Outputs:** Draft claim record and draft line item records.
- **Business rules:**
  - Only users with active enrollment for selected plan year may create claim drafts.
  - Service date must be within plan year or grace period.
- **Acceptance criteria:**
  - Given valid enrollment and inputs, draft saves without claim submission.
  - Each line is persisted with unique line identifier.
- **Dependencies:** Enrollment wizard (eligibility/plan-year context), Admin configuration (plan-year window rules), Audit logs.
- **Open questions:** Should draft auto-save occur on field blur, time interval, or explicit save only?

### FR-CB-002
- **Description:** The system shall support selecting previously saved receipt/expense drafts and attaching them to a claim before submission.
- **Priority:** Must
- **Actor:** Employee
- **Inputs:** Draft expense IDs, claim draft ID.
- **Outputs:** Claim-to-expense associations.
- **Business rules:**
  - One expense draft may be linked to at most one submitted claim line.
  - Detached items remain in receipt locker in draft state.
- **Acceptance criteria:**
  - Employee can add/remove saved expenses before submission.
  - Association changes are reflected immediately in claim totals.
- **Dependencies:** Receipt locker, Document upload and validation, Audit logs.
- **Open questions:** Is many-to-one merging of receipt drafts into one line allowed?

### FR-CB-003
- **Description:** The system shall validate claim and line completeness before submission and block submission when required data or documents are missing.
- **Priority:** Must
- **Actor:** Employee
- **Inputs:** Claim draft payload, document checklist results.
- **Outputs:** Submission success with claim ID or validation error list.
- **Business rules:**
  - Required documents are determined by category-specific policy.
  - Validation errors must be line-specific and actionable.
- **Acceptance criteria:**
  - Incomplete lines are highlighted with missing requirements.
  - Submission succeeds only when all mandatory conditions pass.
- **Dependencies:** Document upload and validation, Admin configuration, Claim status dashboard.
- **Open questions:** Should warnings (non-blocking) be supported separately from blocking errors?

---

## 2) Document Upload and Validation

### FR-DUV-001
- **Description:** The system shall support secure upload of receipt/evidence files (image/PDF) and bind each file to a claim line, receipt draft, appeal, or denial-repair request.
- **Priority:** Must
- **Actor:** Employee, Reviewer
- **Inputs:** File binary, MIME type, contextual entity ID.
- **Outputs:** Stored file object metadata and linkage record.
- **Business rules:**
  - Accept only configured file types and size limits.
  - Reject corrupted/unreadable uploads with explicit error messaging.
- **Acceptance criteria:**
  - Valid files are stored and retrievable by authorized users.
  - Invalid files are rejected with reason code.
- **Dependencies:** Admin configuration, Receipt locker, Appeals, Denial repair, Audit logs.
- **Open questions:** Are HEIC and multi-page TIFF required support formats?

### FR-DUV-002
- **Description:** The system shall run policy-driven documentation checks by expense type (including OTC-specific conditional evidence requirements).
- **Priority:** Must
- **Actor:** System
- **Inputs:** Expense category, extracted/OCR metadata, attached documents.
- **Outputs:** Per-line documentation status and unmet requirement list.
- **Business rules:**
  - OTC lines require supplemental product evidence when receipt detail is insufficient.
  - Rules are versioned by plan year.
- **Acceptance criteria:**
  - OTC submissions are blocked only when conditional supplemental evidence is required and missing.
  - Documentation-complete status is recalculated on each file update.
- **Dependencies:** Claim builder, Admin configuration, Denial repair.
- **Open questions:** What confidence threshold for OCR should trigger manual supplemental prompt?

---

## 3) Receipt Locker

### FR-RL-001
- **Description:** The system shall provide a receipt locker where employees can store expense drafts before claim submission and view threshold progress.
- **Priority:** Must
- **Actor:** Employee
- **Inputs:** Expense metadata, receipt file, plan year context.
- **Outputs:** Saved expense draft and updated threshold-progress indicator.
- **Business rules:**
  - Saving to locker must not create a submitted claim.
  - Duplicate detection should flag likely duplicate receipts.
- **Acceptance criteria:**
  - User receives in-app confirmation for saved drafts.
  - Threshold progress reflects all current draft expenses.
- **Dependencies:** Claim builder, Document upload and validation, Claim status dashboard, Audit logs.
- **Open questions:** Which duplicate-detection method is required (hash-only vs metadata + perceptual)?

### FR-RL-002
- **Description:** The system shall allow employees to edit, replace documents, or delete receipt drafts until attached to a submitted claim.
- **Priority:** Should
- **Actor:** Employee
- **Inputs:** Draft ID, revised metadata, replacement file.
- **Outputs:** Updated draft version history.
- **Business rules:**
  - Changes after submission must occur through denial repair or appeal workflows.
- **Acceptance criteria:**
  - Pre-submission draft edits persist and update downstream claim builder views.
- **Dependencies:** Audit logs, Claim builder.
- **Open questions:** Should soft-delete retention period be configurable?

---

## 4) Enrollment Wizard

### FR-EW-001
- **Description:** The system shall provide annual re-enrollment workflow requiring explicit employee submission for the new plan year.
- **Priority:** Must
- **Actor:** Employee
- **Inputs:** Eligibility context, dependent info, election amount, attestations.
- **Outputs:** Enrollment submission record for upcoming plan year.
- **Business rules:**
  - Re-enrollment is never automatic.
  - Election must be within configured min/max limits for plan year.
- **Acceptance criteria:**
  - Successful submission returns confirmation with plan year and election amount.
  - Submission is blocked after enrollment window closes.
- **Dependencies:** Admin configuration, Notifications subsystem, Audit logs.
- **Open questions:** Are mid-window corrections allowed without operations override?

### FR-EW-002
- **Description:** The system shall support draft enrollment save/resume and deadline reminders for incomplete drafts.
- **Priority:** Should
- **Actor:** Employee
- **Inputs:** Partial enrollment draft data, reminder schedule config.
- **Outputs:** Restorable enrollment draft and reminder notifications.
- **Business rules:**
  - Reminder cadence follows configurable policy.
- **Acceptance criteria:**
  - Employee can resume draft from same step with prior answers intact.
- **Dependencies:** Notifications subsystem, Admin configuration.
- **Open questions:** What channels are required (email, SMS, in-app)?

---

## 5) Claim Status Dashboard

### FR-CSD-001
- **Description:** The system shall provide a timeline/status dashboard showing lifecycle events from draft through adjudication, payment, denial, and appeal.
- **Priority:** Must
- **Actor:** Employee, Reviewer, Admin
- **Inputs:** Claim events, status transitions, SLA milestones.
- **Outputs:** Chronological claim timeline and current status.
- **Business rules:**
  - Timeline entries are immutable once posted.
  - Visibility is role-based.
- **Acceptance criteria:**
  - New submission appears immediately with claim ID and submitted timestamp.
  - Pending employee action displays due date and checklist.
- **Dependencies:** Reviewer work queue, Denial repair, Appeals, Batch exports, Audit logs.
- **Open questions:** Should line-level statuses be summarized and expandable by default?

---

## 6) Reviewer Work Queue

### FR-RWQ-001
- **Description:** The system shall provide reviewer queue views for Submitted and Under Review claims with prioritization by age/SLA and filters by status, plan year, and deficiency type.
- **Priority:** Must
- **Actor:** Reviewer
- **Inputs:** Queue filter params, sorting rules.
- **Outputs:** Filtered review queue and claim workload metrics.
- **Business rules:**
  - Queue ordering must surface SLA-at-risk claims first.
- **Acceptance criteria:**
  - Reviewer can open claim, inspect line evidence, and take review action.
- **Dependencies:** Claim status dashboard, Reporting, Admin configuration.
- **Open questions:** Is assignment model pooled, manual, or auto-routed by rule?

### FR-RWQ-002
- **Description:** The system shall allow reviewers to issue missing-document requests using standardized line-level reason codes and policy-bound due dates.
- **Priority:** Must
- **Actor:** Reviewer
- **Inputs:** Claim/line IDs, reason codes, notes, due date.
- **Outputs:** Pending Employee Action status transition and outbound request message.
- **Business rules:**
  - Reason code selection is mandatory.
  - Due date must fall within configured bounds.
- **Acceptance criteria:**
  - Employee receives actionable checklist with exact missing items.
  - Request action is fully auditable.
- **Dependencies:** Denial repair, Notifications subsystem, Admin configuration, Audit logs.
- **Open questions:** Must custom free-text reasons be constrained by template library?

---

## 7) Denial Repair

### FR-DR-001
- **Description:** The system shall allow employees to fulfill missing-document requests by uploading required documents and resubmitting the claim without creating a new claim.
- **Priority:** Must
- **Actor:** Employee
- **Inputs:** Request ID, document uploads, optional explanatory notes.
- **Outputs:** Resubmission event; claim routed back to reviewer queue.
- **Business rules:**
  - Resubmission is blocked until all required checklist items are complete.
  - Prior/replaced documents remain preserved in history.
- **Acceptance criteria:**
  - Claim status changes from Pending Employee Action to Under Review on valid resubmission.
- **Dependencies:** Reviewer work queue, Document upload and validation, Claim status dashboard, Audit logs.
- **Open questions:** Should expired requests auto-close claim lines or route to supervisor review?

### FR-DR-002
- **Description:** The system shall support reviewer denial issuance with structured reason taxonomy, rationale text, and appeal deadline calculation.
- **Priority:** Must
- **Actor:** Reviewer
- **Inputs:** Denied line IDs, reason codes, rationale.
- **Outputs:** Denial record, denial notice payload, appeal window dates.
- **Business rules:**
  - Denial cannot be finalized without reason code and rationale.
  - Appeal deadline clock starts from notice issuance/receipt policy.
- **Acceptance criteria:**
  - Denial notice is reproducible from stored template inputs.
- **Dependencies:** Appeals, Admin configuration, Notifications subsystem, Audit logs.
- **Open questions:** Is supervisor approval mandatory for specific denial categories?

---

## 8) Appeals

### FR-APP-001
- **Description:** The system shall allow employees to submit appeals for denied claims within the configured filing window.
- **Priority:** Must
- **Actor:** Employee
- **Inputs:** Denial/claim reference, written statement, supporting files, submission timestamp.
- **Outputs:** Appeal case ID, Under Appeal Review status, SLA milestones.
- **Business rules:**
  - Appeals filed after deadline are rejected with explicit reason.
  - Written statement is required.
- **Acceptance criteria:**
  - On-time complete submissions create linked appeal case instantly.
  - Late submissions receive deterministic rejection response.
- **Dependencies:** Denial repair, Document upload and validation, Claim status dashboard, Reviewer work queue.
- **Open questions:** Is one appeal per denied line required or one case per claim denial sufficient?

---

## 9) Batch Exports

### FR-BE-001
- **Description:** The system shall generate reimbursement batches for approved, unpaid claim lines using configurable cutoff criteria and preflight validations.
- **Priority:** Must
- **Actor:** Admin/Operations
- **Inputs:** Cycle date/range, inclusion rules, exclusion overrides.
- **Outputs:** Immutable batch record and payment export artifact.
- **Business rules:**
  - Selection must be deterministic and reproducible.
  - Preflight failures block finalization until resolved.
- **Acceptance criteria:**
  - Batch summary lists inclusions/exclusions and validation outcomes.
  - Finalized batch cannot be edited; only superseded by new corrective batch.
- **Dependencies:** Admin configuration, Audit logs, Reporting.
- **Open questions:** Final rule for cycle anchor date (15th vs 25th) and holiday adjustment?

### FR-BE-002
- **Description:** The system shall track transmission and reconciliation states for each batch and surface exception handling workflows.
- **Priority:** Should
- **Actor:** Admin/Operations
- **Inputs:** Transmission metadata, downstream acknowledgment files.
- **Outputs:** Batch state transitions (Generated → Transmitted → Reconciled/Failed).
- **Business rules:**
  - State transitions must be append-only with timestamped operator/system actor.
- **Acceptance criteria:**
  - Failed transmissions generate exception queue entries and notifications.
- **Dependencies:** Claim status dashboard, Reporting, Notifications subsystem.
- **Open questions:** Which downstream protocol(s) are in scope (SFTP/API/manual upload)?

---

## 10) Reporting

### FR-REP-001
- **Description:** The system shall support operational report generation with filters, date ranges, and Office 2013-compatible Excel output.
- **Priority:** Must
- **Actor:** Admin/Reporting Staff
- **Inputs:** Report template ID, filter set, date range, output format.
- **Outputs:** Downloadable report file(s) and execution metadata.
- **Business rules:**
  - Permission checks required before data export.
  - Oversized synchronous jobs must be queued asynchronously.
- **Acceptance criteria:**
  - Exported Excel opens in Office 2013 and matches selected filters/totals.
- **Dependencies:** Admin configuration, Audit logs.
- **Open questions:** Required retention period and encryption policy for generated files?

---

## 11) Admin Configuration

### FR-AC-001
- **Description:** The system shall provide configuration management for plan-year rules including eligibility windows, contribution limits, documentation requirements, due-date bounds, denial taxonomy, appeal windows, and batch logic.
- **Priority:** Must
- **Actor:** Admin
- **Inputs:** Rule definitions, effective dates, version comments.
- **Outputs:** Versioned configuration sets with activation status.
- **Business rules:**
  - Rule changes are versioned and non-destructive.
  - Active rules are selected by plan year and effective date.
- **Acceptance criteria:**
  - Functional modules consume active configuration without code deploy.
  - Prior versions remain queryable for audit/replay.
- **Dependencies:** All functional modules, Audit logs.
- **Open questions:** Is dual-control (maker-checker) approval required for production config changes?

---

## 12) Audit Logs

### FR-AL-001
- **Description:** The system shall record auditable events for all material actions (create/update/submit/review/deny/appeal/export/config change/batch transmission).
- **Priority:** Must
- **Actor:** System
- **Inputs:** Event payloads from all modules.
- **Outputs:** Immutable audit events with actor, timestamp, entity IDs, before/after references.
- **Business rules:**
  - Logs must be tamper-evident and append-only.
  - Access to log search is role-restricted.
- **Acceptance criteria:**
  - Every requirement above has corresponding auditable events.
  - Investigators can reconstruct lifecycle of claim, line, and related artifacts.
- **Dependencies:** All modules.
- **Open questions:** Required retention period and legal hold workflow?

---

## Traceability Note
Requirement IDs are intended to map to backlog epics/stories and test case IDs. Recommended convention: `FR-<MODULE>-###` links to `TC-<MODULE>-###` and `API-<MODULE>-###` artifacts.
