# HCFSA First Vertical Slice — Target Stack Plan

## Purpose

This document records the target implementation stack and the smallest safe documentation-level plan for the first HCFSA claim vertical slice. It is intentionally limited to planning and documentation; no production application code is introduced by this plan.

## Target stack

- **Web frontend:** React with TypeScript for the employee claim workspace, form validation, API client, and status/validation presentation.
- **Backend:** .NET / ASP.NET Core Web API for REST endpoints, claim orchestration, validation, authorization boundaries, and audit-event creation.
- **Database:** Microsoft SQL Server using reviewed T-SQL migrations and SQL Server-native data types for claim, expense, document metadata, enrollment, plan-year, and audit records.
- **Compatibility posture:** Existing Python/SQLite files in this repository remain a prototype/reference implementation until the React/.NET/T-SQL stack reaches parity for the first vertical slice.

## Current repository baseline

The repository currently contains:

- Documentation under `docs/` describing product scope, API contracts, business rules, domain model, legacy outputs, current-state operations, and target-state journeys.
- A Python standard-library prototype under `hcfsa/` that models the first claim vertical slice.
- SQLite migration SQL under `migrations/`.
- Python `unittest` coverage under `tests/`.

The target stack will be introduced in a future implementation change. Until then, the current prototype should be treated as executable behavior documentation, not the final technology choice.

## First vertical slice scope

The first React/.NET/T-SQL implementation should support only the following employee claim workflow:

1. Employee creates a draft HCFSA claim.
2. Employee adds one claim expense.
3. Employee attaches supporting document metadata to the expense.
4. System validates required claim, expense, and document metadata fields.
5. Employee submits the claim.
6. System records audit events for create, expense add, document attach, validation failure when applicable, and submit.

The first slice explicitly excludes:

- Payment processing.
- Payroll integration.
- Real file binary storage unless a compliant storage service is separately introduced.
- Replacement of LeapFILE, legacy FSA ledgers, payment rails, or back-office legacy processes.
- Claim adjudication, denial repair, appeals, OCR, malware scanning, and export generation beyond metadata required for future compatibility.

## Proposed future project layout

The implementation should use a clear separation between frontend, backend, database, and tests:

```text
frontend/                     React + TypeScript employee UI
backend/Hcfsa.Api/            ASP.NET Core Web API
backend/Hcfsa.Api.Tests/      .NET integration/unit tests
database/migrations/          Reviewed T-SQL migrations
docs/                         Product, architecture, and contract documentation
```

## Backend implementation guidance

The .NET API should expose the documented `/api/v1` REST boundary and keep orchestration separate from infrastructure integrations. For the first slice, the API should implement:

- `POST /api/v1/claims`
- `GET /api/v1/claims/{claim_id}`
- `POST /api/v1/claims/{claim_id}/expenses`
- `POST /api/v1/claims/{claim_id}/expenses/{expense_id}/documents` for metadata-only attachment in the first slice
- `POST /api/v1/claims/{claim_id}/validate`
- `POST /api/v1/claims/{claim_id}/submit`
- `GET /api/v1/claims/{claim_id}/status`
- `GET /api/v1/audit-events?entity_type=claim&entity_id={claim_id}`

The service layer should remain responsible for claim lifecycle rules, document metadata validation, draft-only edit enforcement, and audit event creation. Payment, payroll, export, OCR, and file-storage integrations should be represented only by explicit non-goals or placeholder interfaces when needed for future extensibility.

## Frontend implementation guidance

The React frontend should provide a narrow employee-facing claim builder for the first slice:

- Draft claim creation entry point.
- Single-expense form with claimant, service date, category, service type, provider/merchant where available, amount charged, and requested reimbursement amount.
- Document metadata form for file name, MIME type, size, checksum when available, and document type.
- Validation summary that maps API error-envelope details to actionable field or line messages.
- Submission confirmation and status display.

Client-side validation may improve usability, but backend validation remains authoritative.

## T-SQL data model guidance

The first SQL Server schema should include the minimum tables needed to enforce the slice safely:

- `Agencies`
- `Employees`
- `PlanYears`
- `Enrollments`
- `Claims`
- `ClaimExpenses`
- `ClaimDocuments` or `Documents` plus `DocumentLinks`
- `AuditEvents`
- Optional `IdempotencyKeys` table for create/submit replay protection

Recommended SQL Server conventions:

- Use `uniqueidentifier` for public resource identifiers.
- Use `datetime2` in UTC for persisted timestamps.
- Use `date` for service dates and plan-year boundaries.
- Use `decimal(18,2)` for money values.
- Use `rowversion` on mutable aggregates such as draft claims.
- Use foreign keys for tenant/agency, employee, claim, expense, document, plan-year, and enrollment relationships.
- Store audit records append-only with a hash chain or equivalent tamper-evidence fields.

## Validation rules for the first slice

The backend must enforce at least these rules:

- Actor may create and access only claims in the actor's tenant/agency scope.
- Employee actor may create and submit only that employee's own claim.
- Claim must remain editable only while in `Draft` status.
- Claim submission requires at least one expense.
- Required expense fields must be present and valid.
- Service date must be within the configured plan-year or grace-period claimable window.
- Requested reimbursement amount must be greater than zero and must not exceed amount charged.
- Documentation-required expenses must have at least one supporting document metadata record before submission.
- Submitting a claim transitions it to `Submitted` and persists `submitted_at`/`SubmittedAtUtc`.
- Mutating actions and failed submission validation must create audit events.

## Test strategy

The first implementation should include automated tests at three levels:

1. **.NET backend integration tests** covering the full happy path and blocking validation cases.
2. **.NET service/unit tests** covering claim lifecycle rules, amount validation, draft lock behavior, owner/tenant authorization, and audit hash-chain creation.
3. **React component/API-client tests** covering form validation, API error-envelope rendering, document metadata entry, and submitted status display.

A future end-to-end browser test should exercise the complete UI path once both the React frontend and .NET API are runnable together.

## Documentation-only status

This document updates the project direction to React, .NET, and T-SQL. It does not add application code, generated projects, package manifests, compiled artifacts, migrations, or runtime dependencies.
