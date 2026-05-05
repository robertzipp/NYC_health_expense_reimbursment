# NYC HCFSA Legacy-Compatible Output Specification

## Purpose
This document defines the back-office outputs required to support legacy-compatible operations for NYC HCFSA reimbursement workflows.

## Compatibility Constraints
- Supported file formats are PDF, CSV, and Excel (`.xlsx`) compatible with Microsoft Office 2013.
- Excel outputs must avoid unsupported or high-risk features:
  - No macros/VBA unless explicitly approved through governance.
  - No Power Query, Power Pivot data models, dynamic arrays, or modern Office-only formulas.
  - Use simple worksheet tables, frozen header rows, and plain list/data validation.
- CSV outputs must remain ingestible by standard ETL jobs and spreadsheet tools.
- All outputs must support secure folder transfer and batch processing.

## Global Conventions

### File Name Convention Standard
`HCFSA_<OUTPUT_CODE>_<PLAN_YEAR>_<YYYYMMDD>_<HHMMSS>_<BATCH_OR_RUN_ID>.<EXT>`

Example:
`HCFSA_PAYMENT_BATCH_2026_20261015_210500_RUN0042.csv`

### Common Technical Controls
- **Timezone for timestamps:** America/New_York in file content; UTC allowed in transport metadata.
- **Character set defaults:** UTF-8 (without BOM) for CSV/manifest; PDF standard embedded fonts; `.xlsx` native OOXML.
- **Line endings (CSV):** CRLF for maximum legacy interoperability.
- **Delimiter (CSV):** Comma (`,`), with double-quote escaping per RFC 4180.
- **Nulls:** Blank values unless consumer requires explicit `NULL` literal.
- **PII handling:** Sensitive fields masked where not required by consumer role.

---

## Output Definitions

## 1) Claim Packet PDF
- **Output code:** `CLAIM_PACKET`
- **File name convention:** `HCFSA_CLAIM_PACKET_<CLAIM_ID>_<YYYYMMDD>_<HHMMSS>.pdf`
- **File type:** PDF/A-1b preferred (or standard PDF if archival profile unavailable).
- **Encoding:** Embedded Unicode fonts; text-searchable output.
- **Required sections:**
  1. Cover sheet (claim ID, employee ID, plan year, submission timestamp)
  2. Claim summary (service dates, amount claimed, recipient/dependent)
  3. Eligibility/policy snapshot used during submission
  4. Attestation/signature block
  5. Attachment index with page references
  6. Reviewer notes section (blank in initial output)
- **Data source:** Claim submission service + document management store + policy engine snapshot.
- **Frequency:** On claim submission and on any materially revised resubmission.
- **Consumer:** Review specialists, appeals panel, records/audit staff.
- **Error handling:**
  - If PDF generation fails, mark claim `PACKET_GEN_FAILED`, enqueue retry (max 3 attempts).
  - After final failure, raise manual work item and notify operations queue.
- **Audit requirements:**
  - Log generation event with claim ID, template version, policy snapshot ID, checksum (SHA-256), actor/system ID.
  - Retain immutable copy and hash in audit store.

## 2) Claim Attachment Manifest
- **Output code:** `ATTACHMENT_MANIFEST`
- **File name convention:** `HCFSA_ATTACHMENT_MANIFEST_<CLAIM_ID>_<YYYYMMDD>_<HHMMSS>.csv`
- **File type:** CSV.
- **Encoding:** UTF-8 (no BOM), CRLF.
- **Required columns:**
  - `claim_id`
  - `attachment_id`
  - `file_name`
  - `document_type`
  - `mime_type`
  - `file_size_bytes`
  - `page_count`
  - `upload_timestamp_et`
  - `uploaded_by`
  - `sha256_checksum`
  - `malware_scan_status`
  - `ocr_status`
- **Data source:** Document intake/upload service and malware/OCR processing logs.
- **Frequency:** Generated with each claim packet and on attachment change.
- **Consumer:** Review team, data ops, audit/compliance.
- **Error handling:**
  - Missing checksum or scan status blocks downstream approval and flags `DOC_INTEGRITY_EXCEPTION`.
  - Partial manifest write triggers atomic rollback and retry.
- **Audit requirements:**
  - Record row count, checksum of manifest file, generation timestamp, and source extraction query/run ID.

## 3) Claim Review Excel File
- **Output code:** `CLAIM_REVIEW`
- **File name convention:** `HCFSA_CLAIM_REVIEW_<TEAM_OR_QUEUE>_<YYYYMMDD>_<HHMMSS>.xlsx`
- **File type:** Excel `.xlsx` (Office 2013 compatible).
- **Encoding:** OOXML workbook.
- **Required sheets/columns:**
  - **Sheet `Claims`** (frozen header row, filter enabled):
    - `claim_id`, `employee_id_masked`, `plan_year`, `submission_date`, `expense_start_date`, `expense_end_date`,
      `amount_claimed`, `amount_eligible_estimate`, `status`, `missing_doc_flag`, `denial_reason_code`,
      `appeal_flag`, `priority`, `assigned_reviewer`
  - **Sheet `Reference`**:
    - Denial reason code list, document type codes, status code definitions.
- **Data source:** Claims DB, workflow/status service, policy validation results.
- **Frequency:** Daily batch and on-demand for supervisor queues.
- **Consumer:** Back-office reviewers and supervisors.
- **Error handling:**
  - If workbook exceeds row threshold, split into sequenced files (`..._PART01.xlsx`).
  - If export fails validation, produce fallback CSV extract with same columns and log warning.
- **Audit requirements:**
  - Capture export requester, applied filters, row count, workbook checksum, and delivery location.

## 4) Enrollment Export
- **Output code:** `ENROLLMENT_EXPORT`
- **File name convention:** `HCFSA_ENROLLMENT_EXPORT_<PLAN_YEAR>_<YYYYMMDD>_<HHMMSS>_<RUN_ID>.csv`
- **File type:** CSV.
- **Encoding:** UTF-8 (no BOM), CRLF.
- **Required columns:**
  - `employee_id`
  - `agency_code`
  - `employment_status`
  - `coverage_effective_date`
  - `enrollment_type` (new/open-enrollment/re-enrollment)
  - `annual_election_amount`
  - `admin_fee_annual`
  - `payroll_deduction_per_period`
  - `plan_year`
  - `submission_timestamp_et`
  - `eligibility_rule_version`
  - `record_status`
- **Data source:** Enrollment wizard submissions + eligibility/policy engine.
- **Frequency:** Nightly batch during active enrollment windows; weekly otherwise.
- **Consumer:** Payroll integration team and enrollment operations.
- **Error handling:**
  - Reject records failing required-field validation into companion reject file.
  - Abort file delivery if duplicate primary keys exceed threshold.
- **Audit requirements:**
  - Store run summary (accepted/rejected counts), reject reasons, and transfer confirmation receipt.

## 5) Payment Batch Export
- **Output code:** `PAYMENT_BATCH`
- **File name convention:** `HCFSA_PAYMENT_BATCH_<PLAN_YEAR>_<YYYYMMDD>_<HHMMSS>_<RUN_ID>.csv`
- **File type:** CSV.
- **Encoding:** UTF-8 (no BOM), CRLF.
- **Required columns:**
  - `payment_batch_id`
  - `claim_id`
  - `employee_id`
  - `payment_method_code`
  - `bank_or_disbursement_account_ref`
  - `approved_amount`
  - `tax_year`
  - `payment_scheduled_date`
  - `approval_timestamp_et`
  - `approver_id`
  - `offset_or_adjustment_flag`
- **Data source:** Approved claims ledger + disbursement scheduling service.
- **Frequency:** Per payment cycle (e.g., daily business-day cutoff).
- **Consumer:** Disbursement/payment processor.
- **Error handling:**
  - Hard stop on negative or zero approved amounts unless adjustment flag is true.
  - Delivery failure triggers retry and prevents status transition to `PAID_SENT`.
- **Audit requirements:**
  - Dual-control trace (preparer/approver IDs), batch hash, total record count, total amount, and transfer receipt ID.

## 6) Denial Reason Report
- **Output code:** `DENIAL_REASON_REPORT`
- **File name convention:** `HCFSA_DENIAL_REASON_REPORT_<YYYYMMDD>_<HHMMSS>_<PERIOD>.xlsx`
- **File type:** Excel `.xlsx` (Office 2013 compatible).
- **Encoding:** OOXML workbook.
- **Required sheets/columns:**
  - **Sheet `Detail`:**
    - `claim_id`, `employee_id_masked`, `denial_reason_code`, `denial_reason_text`, `denial_date`,
      `reviewer_id`, `correctable_flag`, `appeal_window_end_date`
  - **Sheet `Summary`:**
    - `denial_reason_code`, `reason_count`, `percent_of_total`
- **Data source:** Claim decision engine + reviewer action logs.
- **Frequency:** Weekly and month-end.
- **Consumer:** Operations management, quality/compliance team.
- **Error handling:**
  - If summary reconciliation fails against detail count, mark report invalid and regenerate.
- **Audit requirements:**
  - Persist filter window, generation user/system, row counts per sheet, and checksum.

## 7) Missing Documentation Report
- **Output code:** `MISSING_DOC_REPORT`
- **File name convention:** `HCFSA_MISSING_DOC_REPORT_<YYYYMMDD>_<HHMMSS>_<QUEUE>.csv`
- **File type:** CSV.
- **Encoding:** UTF-8 (no BOM), CRLF.
- **Required columns:**
  - `claim_id`
  - `employee_id_masked`
  - `required_document_type`
  - `missing_since_date`
  - `days_outstanding`
  - `outreach_status`
  - `next_followup_date`
  - `assigned_queue`
- **Data source:** Document rules engine + communication/outreach tracker.
- **Frequency:** Daily.
- **Consumer:** Outreach team and review queue coordinators.
- **Error handling:**
  - Claims with unresolved doc-type mapping are routed to exception queue and excluded from outbound report.
- **Audit requirements:**
  - Log excluded exceptions and include exception count in report metadata entry.

## 8) Appeals Report
- **Output code:** `APPEALS_REPORT`
- **File name convention:** `HCFSA_APPEALS_REPORT_<YYYYMMDD>_<HHMMSS>_<PERIOD>.xlsx`
- **File type:** Excel `.xlsx` (Office 2013 compatible).
- **Encoding:** OOXML workbook.
- **Required sheets/columns:**
  - **Sheet `Appeals`:**
    - `appeal_id`, `claim_id`, `employee_id_masked`, `original_denial_code`, `appeal_submitted_date`,
      `appeal_status`, `panel_decision`, `decision_date`, `sla_days`, `sla_breach_flag`
  - **Sheet `Aging`:**
    - bucketed counts (0–7, 8–14, 15–30, 31+ days).
- **Data source:** Appeals workflow service + denial records.
- **Frequency:** Weekly and pre-panel meeting on demand.
- **Consumer:** Appeals panel, compliance, and operations leadership.
- **Error handling:**
  - If SLA calculation input missing dates, set `sla_breach_flag=UNKNOWN` and emit data quality warning log.
- **Audit requirements:**
  - Track who ran export, selected period, and any records with `UNKNOWN` SLA status.

## 9) Audit Export
- **Output code:** `AUDIT_EXPORT`
- **File name convention:** `HCFSA_AUDIT_EXPORT_<YYYYMMDD>_<HHMMSS>_<SCOPE>.csv`
- **File type:** CSV (primary) plus optional PDF cover memo.
- **Encoding:** UTF-8 (no BOM), CRLF.
- **Required columns:**
  - `event_id`
  - `event_timestamp_utc`
  - `event_timestamp_et`
  - `entity_type`
  - `entity_id`
  - `action_type`
  - `actor_type` (user/system)
  - `actor_id`
  - `before_value_hash`
  - `after_value_hash`
  - `source_ip`
  - `correlation_id`
  - `export_run_id`
- **Data source:** Immutable audit/event store.
- **Frequency:** On demand for investigations; scheduled monthly archive.
- **Consumer:** Internal audit, external auditors, legal/compliance.
- **Error handling:**
  - If source event store unavailable, fail closed (no partial export) and raise Sev2 operational alert.
- **Audit requirements:**
  - Meta-audit required: each audit export itself must generate a new audit event capturing requester, scope, approval ticket, and file hash.

---

## Secure Folder Transfer Requirements (Applies to all deliverables)
- Transport mechanism: SFTP to approved partner folder endpoints.
- Delivery pattern: write to temporary filename (`.part`), then atomic rename on completion.
- Companion control file for each batch (optional but recommended):
  - `<base_filename>.ctl` containing record count, file size, SHA-256 checksum, and creation timestamp.
- PGP encryption at file level when destination requires it.
- Retry policy: exponential backoff, max 5 attempts, then operational alert.
- Duplicate protection: idempotent run IDs + consumer-side checksum verification.

## Batch Processing and Manual Review Integration
- All scheduled outputs must run under orchestrated batch jobs with run IDs and deterministic filter windows.
- Each batch run must publish:
  - start/end timestamps,
  - selection criteria,
  - source snapshot/version IDs,
  - success/failure status,
  - output artifact inventory.
- Manual review queues should consume claim review, missing documentation, denial, and appeals outputs with stable key columns (`claim_id`, `appeal_id`, `employee_id_masked`) to allow offline triage and re-upload alignment.
