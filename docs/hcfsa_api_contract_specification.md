# HCFSA API Contract Specification (REST)

## 1) Conventions

- **Base URL:** `/api/v1`
- **AuthN/AuthZ:** OAuth2/JWT bearer token; actor permissions enforced per endpoint.
- **Actors:**
  - `employee`
  - `employer_admin`
  - `reviewer`
  - `finance_admin`
  - `system_integrator`
- **Common headers:**
  - `Authorization: Bearer <token>`
  - `Idempotency-Key` required on mutating create/submit endpoints.
  - `X-Correlation-Id` optional for tracing.
- **Date format:** ISO-8601 (`YYYY-MM-DD` or RFC3339 timestamps).
- **Money format:**
  ```json
  { "amount": "123.45", "currency": "USD" }
  ```
- **Pagination:** `page`, `page_size` query params; response includes `meta`.
- **Resource IDs:** UUID v4 strings.
- **Error envelope (all non-2xx):**
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Human readable summary",
      "details": [{"field":"service_date","issue":"must be within plan year"}],
      "correlation_id": "..."
    }
  }
  ```


## 1.1 Target Implementation Stack

- **Client:** React with TypeScript consumes this REST contract through an API client layer.
- **Server:** .NET / ASP.NET Core Web API owns request validation, authorization checks, claim workflow orchestration, and audit-event emission.
- **Database:** Microsoft SQL Server persists workflow state using T-SQL migrations and SQL Server-native constraints.
- **First-slice document handling:** Until compliant binary storage is introduced, document endpoints in the first vertical slice may attach metadata only and must not imply that file bytes are durably stored by the application.

## 2) Standard Error Codes

- `400 VALIDATION_ERROR`
- `401 UNAUTHENTICATED`
- `403 FORBIDDEN`
- `404 NOT_FOUND`
- `409 CONFLICT`
- `412 PRECONDITION_FAILED`
- `422 BUSINESS_RULE_VIOLATION`
- `429 RATE_LIMITED`
- `500 INTERNAL_ERROR`

---

## 3) Endpoint Contracts

## 3.1 Employee Profile

### GET `/employees/{employee_id}/profile`
- **Actor permissions:** `employee` (self), `employer_admin` (same org), `reviewer` (read-only)
- **Request body:** none
- **Response body (200):**
  ```json
  {
    "employee_id": "uuid",
    "first_name": "Ava",
    "last_name": "Lee",
    "email": "ava@example.com",
    "dob": "1989-06-14",
    "hire_date": "2023-01-10",
    "employment_status": "active",
    "address": {"line1":"...","city":"...","state":"NY","postal_code":"10001"},
    "updated_at": "2026-05-05T10:15:00Z"
  }
  ```
- **Validation rules:** requester must have scoped access to `employee_id`.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `employee_profile.viewed`.

### PATCH `/employees/{employee_id}/profile`
- **Actor permissions:** `employee` (self), `employer_admin`
- **Request body:** partial profile fields (`email`, `address`, phone, communication prefs)
- **Response body (200):** updated profile object.
- **Validation rules:** email RFC format; immutable fields (`dob`, `hire_date`) rejected unless admin override policy.
- **Error responses:** `400`, `401`, `403`, `404`, `409`.
- **Audit events generated:** `employee_profile.updated`.

## 3.2 Plan Year Configuration

### GET `/plan-years/{plan_year_id}`
- **Actor permissions:** `employee`, `employer_admin`, `reviewer`, `finance_admin`
- **Request body:** none
- **Response body (200):**
  ```json
  {
    "plan_year_id":"uuid",
    "name":"2026",
    "start_date":"2026-01-01",
    "end_date":"2026-12-31",
    "runout_end_date":"2027-03-31",
    "max_election":{"amount":"3300.00","currency":"USD"},
    "grace_period_days":0,
    "status":"active"
  }
  ```
- **Validation rules:** visible only to same tenant.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `plan_year.viewed`.

### PUT `/plan-years/{plan_year_id}`
- **Actor permissions:** `employer_admin`
- **Request body:** full config payload.
- **Response body (200):** saved config.
- **Validation rules:** `start_date < end_date`; `runout_end_date >= end_date`; max election within statutory constraints.
- **Error responses:** `400`, `401`, `403`, `404`, `422`, `409` (immutable if locked).
- **Audit events generated:** `plan_year.updated`.

## 3.3 Enrollment (create/read/update/submit)

### POST `/enrollments`
- **Actor permissions:** `employee`, `employer_admin`
- **Request body:**
  ```json
  {"employee_id":"uuid","plan_year_id":"uuid","election":{"amount":"1800.00","currency":"USD"}}
  ```
- **Response body (201):** enrollment with `status: "draft"`.
- **Validation rules:** one active enrollment per employee+plan_year; election > 0 and <= plan max.
- **Error responses:** `400`, `401`, `403`, `409`, `422`.
- **Audit events generated:** `enrollment.created`.

### GET `/enrollments/{enrollment_id}`
- **Actor permissions:** `employee` (owner), `employer_admin`, `reviewer`
- **Request body:** none
- **Response body (200):** enrollment object.
- **Validation rules:** scope checks.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `enrollment.viewed`.

### PATCH `/enrollments/{enrollment_id}`
- **Actor permissions:** `employee` (owner), `employer_admin`
- **Request body:** mutable fields (`election.amount`, recipients, acknowledgements).
- **Response body (200):** updated draft.
- **Validation rules:** only `draft` status editable; election within plan bounds.
- **Error responses:** `400`, `401`, `403`, `404`, `409`, `422`.
- **Audit events generated:** `enrollment.updated`.

### POST `/enrollments/{enrollment_id}/submit`
- **Actor permissions:** `employee` (owner), `employer_admin`
- **Request body:** optional attestation object.
- **Response body (200):** enrollment `status: "submitted"`, `submitted_at`.
- **Validation rules:** required attestations present; enrollment complete.
- **Error responses:** `400`, `401`, `403`, `404`, `409`, `422`.
- **Audit events generated:** `enrollment.submitted`.

## 3.4 Eligible Recipients

### GET `/employees/{employee_id}/eligible-recipients`
- **Actor permissions:** `employee` (self), `reviewer`, `employer_admin`
- **Request body:** none
- **Response body (200):** array of recipient records (self/spouse/dependents) with eligibility window.
- **Validation rules:** recipient records must belong to employee.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `recipient.viewed`.

### POST `/employees/{employee_id}/eligible-recipients`
- **Actor permissions:** `employee` (self), `employer_admin`
- **Request body:** recipient demographics and relationship.
- **Response body (201):** created recipient.
- **Validation rules:** valid relationship enum; dependent DOB rules.
- **Error responses:** `400`, `401`, `403`, `404`, `422`.
- **Audit events generated:** `recipient.created`.

## 3.5 Receipt Locker

### GET `/employees/{employee_id}/receipt-locker`
- **Actor permissions:** `employee` (self), `reviewer`
- **Request body:** none
- **Response body (200):** paginated receipt metadata.
- **Validation rules:** tenant and owner scope.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `receipt_locker.viewed`.

## 3.6 Claim (create/read/update/submit)

### POST `/claims`
- **Actor permissions:** `employee`, `employer_admin`
- **Request body:**
  ```json
  {"employee_id":"uuid","plan_year_id":"uuid","recipient_id":"uuid","service_start":"2026-02-01","service_end":"2026-02-01"}
  ```
- **Response body (201):** claim with `status: "draft"`.
- **Validation rules:** service dates in claimable period; recipient eligible.
- **Error responses:** `400`, `401`, `403`, `422`.
- **Audit events generated:** `claim.created`.

### GET `/claims/{claim_id}`
- **Actor permissions:** `employee` (owner), `reviewer`, `employer_admin`, `finance_admin`
- **Response body (200):** claim aggregate with expenses, documents, status timeline.
- **Validation rules:** scoped access.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `claim.viewed`.

### PATCH `/claims/{claim_id}`
- **Actor permissions:** `employee` (owner), `employer_admin`
- **Request body:** mutable claim metadata in draft.
- **Response body (200):** updated claim.
- **Validation rules:** only `draft` editable by employee; locked after submission.
- **Error responses:** `400`, `401`, `403`, `404`, `409`.
- **Audit events generated:** `claim.updated`.

### POST `/claims/{claim_id}/submit`
- **Actor permissions:** `employee` (owner), `employer_admin`
- **Request body:** optional final attestation.
- **Response body (200):** `status: "submitted"`.
- **Validation rules:** at least one expense line; documentation requirements satisfied.
- **Error responses:** `400`, `401`, `403`, `404`, `409`, `422`.
- **Audit events generated:** `claim.submitted`.

## 3.7 Claim Expense Management

### POST `/claims/{claim_id}/expenses`
- **Actor permissions:** `employee` (owner), `employer_admin`
- **Request body:** merchant/provider, category, service_date, amount, notes.
- **Response body (201):** expense line.
- **Validation rules:** amount > 0; service date in eligible window; category allowed.
- **Error responses:** `400`, `401`, `403`, `404`, `422`.
- **Audit events generated:** `claim_expense.created`.

### PATCH `/claims/{claim_id}/expenses/{expense_id}`
- **Actor permissions:** `employee` (owner), `employer_admin`
- **Request body:** mutable expense fields.
- **Response body (200):** updated expense.
- **Validation rules:** draft-only edits.
- **Error responses:** `400`, `401`, `403`, `404`, `409`.
- **Audit events generated:** `claim_expense.updated`.

### DELETE `/claims/{claim_id}/expenses/{expense_id}`
- **Actor permissions:** `employee` (owner), `employer_admin`
- **Request body:** none
- **Response body (204):** empty.
- **Validation rules:** draft-only delete.
- **Error responses:** `401`, `403`, `404`, `409`.
- **Audit events generated:** `claim_expense.deleted`.

## 3.8 Document Upload

### POST `/documents/uploads`
- **Actor permissions:** `employee`, `employer_admin`, `reviewer`
- **Request body:** filename, mime_type, size_bytes, checksum; optional `claim_id`.
- **Response body (201):** pre-signed upload target + `document_id`.
- **Validation rules:** allowed mime types (`application/pdf`, `image/jpeg`, `image/png`, `image/heic`); size <= configured max.
- **Error responses:** `400`, `401`, `403`, `413`, `422`.
- **Audit events generated:** `document.upload_initiated`.

### POST `/documents/{document_id}/finalize`
- **Actor permissions:** uploader identity
- **Request body:** storage key, checksum confirmation.
- **Response body (200):** document metadata with `status: "available"`.
- **Validation rules:** checksum match; upload must exist and not expired.
- **Error responses:** `400`, `401`, `403`, `404`, `409`, `422`.
- **Audit events generated:** `document.upload_finalized`.

## 3.9 Claim Status

### GET `/claims/{claim_id}/status`
- **Actor permissions:** `employee` (owner), `reviewer`, `finance_admin`, `employer_admin`
- **Response body (200):** current status + timeline events.
- **Validation rules:** scoped access.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `claim_status.viewed`.

## 3.10 Missing Information Requests

### POST `/claims/{claim_id}/missing-information-requests`
- **Actor permissions:** `reviewer`
- **Request body:** requested fields/documents, due_date, message.
- **Response body (201):** request object with `status: "open"`.
- **Validation rules:** claim must be in reviewable state.
- **Error responses:** `400`, `401`, `403`, `404`, `409`.
- **Audit events generated:** `missing_info_request.created`.

### POST `/missing-information-requests/{request_id}/respond`
- **Actor permissions:** `employee` (claim owner)
- **Request body:** answers + attachments references.
- **Response body (200):** request `status: "responded"`.
- **Validation rules:** request must be open and not expired.
- **Error responses:** `400`, `401`, `403`, `404`, `409`, `422`.
- **Audit events generated:** `missing_info_request.responded`.

## 3.11 Review Queue

### GET `/review-queue/claims`
- **Actor permissions:** `reviewer`
- **Request body:** none (supports filters via query params)
- **Response body (200):** paginated claims with SLA metadata.
- **Validation rules:** reviewer role required.
- **Error responses:** `401`, `403`.
- **Audit events generated:** `review_queue.viewed`.

## 3.12 Reviewer Decisions

### POST `/claims/{claim_id}/decisions`
- **Actor permissions:** `reviewer`
- **Request body:**
  ```json
  {
    "decision":"approved|partially_approved|denied",
    "approved_amount":{"amount":"95.00","currency":"USD"},
    "reason_codes":["INSUFFICIENT_DOCUMENTATION"],
    "notes":"..."
  }
  ```
- **Response body (201):** decision object + updated claim status.
- **Validation rules:** one terminal decision per review cycle; approved amount <= claimed amount.
- **Error responses:** `400`, `401`, `403`, `404`, `409`, `422`.
- **Audit events generated:** `claim.decision_recorded`.

## 3.13 Appeals

### POST `/claims/{claim_id}/appeals`
- **Actor permissions:** `employee` (owner)
- **Request body:** rationale, supporting documents.
- **Response body (201):** appeal record `status: "submitted"`.
- **Validation rules:** appeal window open; claim has eligible prior decision.
- **Error responses:** `400`, `401`, `403`, `404`, `409`, `422`.
- **Audit events generated:** `appeal.submitted`.

### POST `/appeals/{appeal_id}/decisions`
- **Actor permissions:** `reviewer` (appeals team)
- **Request body:** `upheld|overturned|modified`, notes, revised amount if applicable.
- **Response body (200):** final appeal decision + claim state.
- **Validation rules:** appeal must be pending; modified amount rules apply.
- **Error responses:** `400`, `401`, `403`, `404`, `409`, `422`.
- **Audit events generated:** `appeal.decided`.

## 3.14 Payment Batches

### POST `/payment-batches`
- **Actor permissions:** `finance_admin`, `system_integrator`
- **Request body:** plan_year filters, cutoff_date, payment_method.
- **Response body (201):** batch with totals and included approved claims.
- **Validation rules:** only payable claims included; no duplicate disbursement.
- **Error responses:** `400`, `401`, `403`, `409`, `422`.
- **Audit events generated:** `payment_batch.created`.

### GET `/payment-batches/{batch_id}`
- **Actor permissions:** `finance_admin`, `reviewer`
- **Response body (200):** batch details + line items + lifecycle status.
- **Validation rules:** tenant scope.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `payment_batch.viewed`.

## 3.15 Exports

### POST `/exports`
- **Actor permissions:** `employer_admin`, `finance_admin`, `system_integrator`
- **Request body:** export type (`claims`, `enrollments`, `audit_events`), filters, format (`csv`,`json`).
- **Response body (202):** async job record with `export_id`.
- **Validation rules:** export type and format enum checks; date range max window.
- **Error responses:** `400`, `401`, `403`, `422`.
- **Audit events generated:** `export.requested`.

### GET `/exports/{export_id}`
- **Actor permissions:** requester role + org admins
- **Response body (200):** job status; download URL when complete.
- **Validation rules:** only requester org access.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `export.viewed`.

## 3.16 Notifications

### POST `/notifications`
- **Actor permissions:** `system_integrator`, internal service principal
- **Request body:** recipient, channel (`email`,`sms`,`in_app`), template_id, variables, related resource refs.
- **Response body (202):** queued notification with tracking ID.
- **Validation rules:** channel policy checks; template exists.
- **Error responses:** `400`, `401`, `403`, `422`.
- **Audit events generated:** `notification.queued`.

### GET `/notifications/{notification_id}`
- **Actor permissions:** `employee` (own), `employer_admin`, `reviewer`
- **Response body (200):** delivery status, attempts, timestamps.
- **Validation rules:** scope checks.
- **Error responses:** `401`, `403`, `404`.
- **Audit events generated:** `notification.viewed`.

## 3.17 Audit Events

### GET `/audit-events`
- **Actor permissions:** `employer_admin`, `finance_admin`, `reviewer` (restricted), `system_integrator`
- **Request body:** none (query filters: actor, resource_type, resource_id, date range)
- **Response body (200):** paginated immutable event records.
- **Validation rules:** PII redaction policy by role; max query range enforced.
- **Error responses:** `401`, `403`, `422`.
- **Audit events generated:** `audit_events.query_executed`.

---

## 4) Cross-Cutting Validation Rules

- Claims cannot exceed remaining available balance for plan year.
- Service dates must be on/after plan year start and on/before runout constraints as configured.
- Submitted claims/enrollments become immutable except through formal correction workflow.
- Every mutating request must include actor context and be idempotent where side effects are possible.

## 5) REST Rationale and Exceptions

- REST used for all primary resources and state transitions.
- **Strong reason exception:** `POST /documents/uploads` returns pre-signed object store upload contract (RPC-like helper) because binary streaming through core API is operationally inferior for large files.
- Long-running operations (`/exports`) use async `202 Accepted` job pattern.


## 6) Pre-Implementation Security, Privacy, Idempotency, Pagination, Upload-Risk, and Auditability Review

This section lists **required changes** to the contracts before implementation.

### 6.1 Security & Authorization

1. **Tenant-bound authorization must be explicit on every endpoint**
   - Add required claims: `tenant_id`, `actor_id`, `actor_type`, `scopes`.
   - Enforce resource tenant match (`resource.tenant_id == token.tenant_id`) server-side for all reads/writes.
   - Add `403` for scope mismatch and `404` masking option for anti-enumeration.

2. **Step-up authentication for sensitive operations**
   - Require recent auth (e.g., last 15 minutes) or MFA step-up for:
     - Profile PII updates
     - Payment batch creation
     - Export creation/download of sensitive datasets
   - Add `401` with code `STEP_UP_REQUIRED` when unmet.

3. **Reviewer and admin segregation of duties**
   - Prevent same user from both deciding claim and approving payment batch containing it.
   - Add `422 BUSINESS_RULE_VIOLATION` for SoD conflicts.

4. **Rate limits and abuse controls**
   - Define per-actor/per-IP limits for create/submit/upload endpoints.
   - Return `429` with `Retry-After`.

### 6.2 Privacy & Data Minimization

1. **Field-level data classification and redaction policy**
   - Mark fields as `public/internal/confidential/restricted`.
   - Mask DOB, address, and dependent PII in reviewer queue/list endpoints unless business-necessary.

2. **Purpose limitation for exports and notifications**
   - Require `purpose` field on `/exports` request and retain it in audit logs.
   - Block or redact restricted fields by default unless explicit elevated scope is present.

3. **Retention and deletion policy contracts**
   - Add metadata fields to document/audit/export resources:
     - `retention_until`
     - `legal_hold` (boolean)
     - `purge_eligible_at`

4. **Secure error payloads**
   - Ensure `details` never contain PHI/PII values; reference field names only.

### 6.3 Idempotency & Concurrency Controls

1. **Idempotency behavior must be fully specified**
   - For endpoints requiring `Idempotency-Key`, define:
     - key scope = `(actor_id, method, path)`
     - TTL (recommended 24h)
     - replay behavior: return original status/body
     - mismatch behavior: `409 IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD`

2. **Optimistic concurrency for mutable resources**
   - Add `ETag` response header on GET for mutable resources.
   - Require `If-Match` on PATCH/submit/decision endpoints.
   - Return `412 PRECONDITION_FAILED` on stale writes.

3. **Duplicate submit prevention**
   - Explicitly make `/submit` endpoints idempotent and safe against retries.
   - Return current submitted state on replays, not duplicate transitions.

### 6.4 Pagination & Query Safety

1. **Cursor pagination for large/volatile collections**
   - Replace offset pagination with cursor for:
     - `/review-queue/claims`
     - `/audit-events`
     - `/employees/{id}/receipt-locker`
   - Add `next_cursor` and stable sort key (`created_at DESC, id DESC`).

2. **Maximum page size and bounded filters**
   - Enforce `page_size <= 200` (or policy value).
   - Require date range bounds (e.g., max 92 days) for costly endpoints.

3. **Deterministic filtering contract**
   - Publish canonical filter operators and type validation (exact, range, enum-only).

### 6.5 File Upload Threat Model Controls

1. **Malware scanning and quarantine lifecycle**
   - Add states: `uploaded -> scanning -> available|rejected`.
   - Claims cannot be submitted if required documents are still `scanning` or `rejected`.

2. **Pre-signed URL hardening**
   - Enforce short expiry (<=15 min), single-use token, fixed object key, content-length-range, and exact `Content-Type`.
   - Bind checksum and reject mismatch at finalize.

3. **Content validation beyond MIME**
   - Validate magic bytes/file signatures; reject polyglot files.
   - Strip active content (macros/scripts) where applicable.

4. **Safe retrieval and rendering**
   - Serve with `Content-Disposition: attachment` for risky formats.
   - Never inline-render untrusted files in privileged reviewer context without sanitization.

5. **PII-safe logging**
   - Do not log filenames containing PHI/PII verbatim; hash or tokenize names in logs.

### 6.6 Auditability & Non-Repudiation

1. **Standardized audit envelope for every mutating action**
   - Required fields:
     - `event_id`, `event_type`, `occurred_at`, `actor_id`, `actor_type`, `tenant_id`
     - `resource_type`, `resource_id`, `action`, `outcome`
     - `correlation_id`, `ip_hash`, `user_agent_hash`, `idempotency_key`

2. **Before/after snapshots with redaction**
   - For updates/decisions, persist changed fields with old/new values (PII redacted or tokenized).

3. **Tamper evidence and immutability**
   - Store audit logs append-only with integrity checks (hash chain or signed batches).

4. **Audit access auditing**
   - Keep `audit_events.query_executed`, but also record query filter metadata and row-count returned.

### 6.7 Endpoint-Level Adjustments Required

- **`POST /documents/uploads`**
  - Add request fields: `document_category`, `claim_id` (required when claim-bound), `declared_hash_algo`.
  - Add responses/errors for scanning lifecycle and policy rejections.

- **`POST /documents/{document_id}/finalize`**
  - Require proof of upload ownership and one-time finalize token.

- **`POST /exports` + `GET /exports/{id}`**
  - Add async states: `queued|running|completed|failed|expired`.
  - Download URLs must be short-lived and single-use; capture downloader identity in audit.

- **`POST /payment-batches`**
  - Require idempotency key and SoD check result in response metadata.

- **`POST /claims/{id}/decisions` and appeal decisions**
  - Require decision reason codes from controlled taxonomy; free-text notes optional.

- **All GET list endpoints**
  - Add explicit `sort`, `cursor`, `limit`, and `include_total` behavior.

### 6.8 Additional Error Codes to Add

- `STEP_UP_REQUIRED` (401)
- `IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_PAYLOAD` (409)
- `MALWARE_DETECTED` (422)
- `DOCUMENT_SCAN_PENDING` (409)
- `DATA_CLASSIFICATION_RESTRICTION` (403)

### 6.9 Minimum Implementation Gate (Definition of Ready)

Before build starts, contracts should include:
- OpenAPI schemas with field-level constraints and enums.
- Explicit auth scope matrix per endpoint and per field where needed.
- Idempotency and concurrency semantics (ETag/If-Match) documented.
- Upload security lifecycle and malware handling.
- Cursor pagination for high-volume collections.
- Audit event schema and retention policy.
