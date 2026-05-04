# HCFSA Platform Domain Model

This domain model defines core entities for a Health Care Flexible Spending Account (HCFSA) platform used by NYC employees and agencies. It is designed to support enrollment, claims processing, reviews, payments, appeals, and compliance reporting.

## Cross-Cutting Notes

- **Tenant boundary:** `agencyId` is a primary partitioning key for most records.
- **Identity boundary:** `employeeId` is the canonical participant key.
- **Financial integrity:** Election and claim/payment records should be immutable after posting, with correction via reversal/adjustment records.
- **PHI/PII handling:** Claims, documents, and recipient data contain sensitive data and should be encrypted at rest and tightly access-controlled.
- **Normalization boundary:** write models should avoid duplicated foreign-key facts when a single authoritative link exists.
- **Lineage and replay:** exports and financial postings should support deterministic replay and immutable sequence history.

---

## 1) Employee

### Purpose
Represents an HCFSA-eligible worker (active, terminated, retired as policy permits) who may enroll and submit claims.

### Key fields
- `employeeId` (string, internal immutable ID)
- `externalEmployeeNumber` (string, HR/payroll key)
- `agencyId` (string)
- `firstName`, `lastName`
- `dateOfBirth` (encrypted vault field)
- `ageBand` (derived, non-sensitive analytic attribute)
- `email`, `phone`
- `employmentStatus` (ACTIVE, LEAVE, TERMINATED)
- `hireDate`, `terminationDate`
- `preferredLanguage`
- `createdAt`, `updatedAt`

### Relationships
- Many Employees belong to one Agency.
- One Employee has many Enrollments, Claims, Notifications, Appeals, and AuditEvents.
- One Employee has many EligibleRecipients.

### Required fields
`employeeId`, `externalEmployeeNumber`, `agencyId`, `firstName`, `lastName`, `employmentStatus`, `createdAt`.

### Sensitive fields
Name, DOB, contact details, external employee number.

### Retention considerations
Retain for statutory payroll/benefits audit period (often 6-7+ years after separation), with legal hold support.

### Example JSON object
```json
{
  "employeeId": "emp_100245",
  "externalEmployeeNumber": "NYC-778123",
  "agencyId": "agency_DOE",
  "firstName": "Jordan",
  "lastName": "Lee",
  "dateOfBirth": "1987-04-22",
  "email": "jordan.lee@agency.nyc.gov",
  "phone": "+1-212-555-0181",
  "employmentStatus": "ACTIVE",
  "hireDate": "2014-09-03",
  "terminationDate": null,
  "preferredLanguage": "en",
  "createdAt": "2026-01-10T15:20:44Z",
  "updatedAt": "2026-03-01T10:09:33Z"
}
```

---

## 2) Agency

### Purpose
Represents a participating NYC agency/employer unit and its operational/payment context.

### Key fields
- `agencyId`
- `agencyCode`
- `name`
- `status`
- `payrollProvider`
- `defaultFundingAccountId`
- `contactEmail`
- `createdAt`

### Relationships
- One Agency has many Employees, PlanYears (if agency-specific), ExportJobs, and AdminConfigurations.

### Required fields
`agencyId`, `agencyCode`, `name`, `status`, `createdAt`.

### Sensitive fields
Operational banking/funding references.

### Retention considerations
Generally long-lived reference data; keep history of code/name changes for auditability.

### Example JSON object
```json
{
  "agencyId": "agency_DOE",
  "agencyCode": "DOE",
  "name": "Department of Education",
  "status": "ACTIVE",
  "payrollProvider": "NYC_PAYROLL",
  "defaultFundingAccountId": "acct_ops_01",
  "contactEmail": "benefits@doe.nyc.gov",
  "createdAt": "2020-01-01T00:00:00Z"
}
```

---

## 3) PlanYear

### Purpose
Defines the coverage and contribution period, regulatory limits, and processing windows.

### Key fields
- `planYearId`
- `name` (e.g., FY2026)
- `startDate`, `endDate`
- `runoutDeadline`
- `maxElectionAmount`
- `gracePeriodEndDate` (if applicable)
- `carryoverLimit` (if applicable)
- `status` (DRAFT, OPEN_ENROLLMENT, ACTIVE, CLOSED)

### Relationships
- One PlanYear has many Enrollments, ContributionElections, Claims, PaymentBatches.

### Required fields
`planYearId`, `startDate`, `endDate`, `runoutDeadline`, `maxElectionAmount`, `status`.

### Sensitive fields
Typically none (configuration-level).

### Retention considerations
Retain permanently or long-term for benefit/audit evidence.

### Example JSON object
```json
{
  "planYearId": "py_2026",
  "name": "Plan Year 2026",
  "startDate": "2026-01-01",
  "endDate": "2026-12-31",
  "runoutDeadline": "2027-03-31",
  "maxElectionAmount": 3300.0,
  "gracePeriodEndDate": null,
  "carryoverLimit": 0.0,
  "status": "ACTIVE"
}
```

---

## 4) Enrollment

### Purpose
Captures an employee’s participation status in a plan year.

### Key fields
- `enrollmentId`
- `employeeId` (derived/read-model mirror of Enrollment)
- `planYearId` (derived/read-model mirror of Enrollment)
- `enrollmentStatus` (PENDING, ACTIVE, WAIVED, TERMINATED)
- `effectiveDate`
- `terminationReason`
- `source` (SELF_SERVICE, HR_FEED, ADMIN)
- `createdAt`

### Relationships
- Many Enrollments per Employee and PlanYear (versioned over time).
- One Enrollment has one or more ContributionElections.

### Required fields
`enrollmentId`, `employeeId`, `planYearId`, `enrollmentStatus`, `effectiveDate`, `createdAt`.

### Sensitive fields
Indirectly sensitive (benefit participation status).

### Retention considerations
Keep with claim/payment history for statutory and tax audit retention.

### Example JSON object
```json
{
  "enrollmentId": "enr_8f20",
  "employeeId": "emp_100245",
  "planYearId": "py_2026",
  "enrollmentStatus": "ACTIVE",
  "effectiveDate": "2026-01-01",
  "terminationReason": null,
  "source": "SELF_SERVICE",
  "createdAt": "2025-11-15T17:31:09Z"
}
```

---

## 5) ContributionElection

### Purpose
Stores elected annual contribution and payroll deduction cadence.

### Key fields
- `electionId`
- `enrollmentId`
- `employeeId` (derived/read-model mirror of Enrollment)
- `planYearId` (derived/read-model mirror of Enrollment)
- `annualElectionAmount`
- `perPayPeriodAmount`
- `payPeriodsPerYear`
- `electionStatus` (PENDING, APPROVED, LOCKED, CHANGED)
- `effectiveFrom`
- `version`

### Relationships
- Many elections may belong to one Enrollment (version history).

### Required fields
`electionId`, `enrollmentId`, `annualElectionAmount`, `payPeriodsPerYear`, `effectiveFrom`, `version`.

### Integrity constraints
- `enrollmentId` is the authoritative relationship for write operations.
- `employeeId` and `planYearId` must either be derived at read time or validated against Enrollment by database constraint/trigger.

### Sensitive fields
Financial deductions.

### Retention considerations
Do not hard-delete; maintain versions for IRS/compliance audits.

### Example JSON object
```json
{
  "electionId": "el_2001_v1",
  "enrollmentId": "enr_8f20",
  "employeeId": "emp_100245",
  "planYearId": "py_2026",
  "annualElectionAmount": 2400.0,
  "perPayPeriodAmount": 100.0,
  "payPeriodsPerYear": 24,
  "electionStatus": "LOCKED",
  "effectiveFrom": "2026-01-01",
  "version": 1
}
```

---

## 6) EligibleRecipient

### Purpose
Represents a person whose care expenses can be reimbursed (employee, spouse, dependent).

### Key fields
- `recipientId`
- `employeeId`
- `relationshipType` (SELF, SPOUSE, CHILD, OTHER_DEPENDENT)
- `firstName`, `lastName`
- `dateOfBirth` (encrypted vault field)
- `ageBand` (derived, non-sensitive analytic attribute)
- `taxDependentFlag`
- `coverageStartDate`, `coverageEndDate`

### Relationships
- One Employee has many EligibleRecipients.
- One EligibleRecipient may be referenced by many ClaimExpenses.

### Required fields
`recipientId`, `employeeId`, `relationshipType`, `firstName`, `lastName`, `dateOfBirth`.

### Sensitive fields
PII and potentially minors’ data.

### Retention considerations
Retain while claims/appeals remain possible plus statutory period.

### Example JSON object
```json
{
  "recipientId": "rec_553",
  "employeeId": "emp_100245",
  "relationshipType": "CHILD",
  "firstName": "Alex",
  "lastName": "Lee",
  "dateOfBirth": "2016-08-13",
  "taxDependentFlag": true,
  "coverageStartDate": "2026-01-01",
  "coverageEndDate": null
}
```

---

## 7) Claim

### Purpose
Top-level reimbursement request submitted by an employee.

### Key fields
- `claimId`
- `employeeId` (derived/read-model mirror of Enrollment)
- `planYearId` (derived/read-model mirror of Enrollment)
- `submittedAt`
- `claimStatus` (SUBMITTED, IN_REVIEW, APPROVED, PARTIALLY_APPROVED, DENIED, PAID)
- `totalAmountSubmitted` (cached aggregate)
- `totalAmountApproved` (cached aggregate)
- `lastRecomputedAt`
- `channel` (WEB, MOBILE, ADMIN)

### Relationships
- One Claim has many ClaimExpenses, DocumentLinks, ReviewTasks, ReviewDecisions.
- One Claim may have one or more PaymentBatchLines.
- One Claim may have zero or many Appeals.

### Required fields
`claimId`, `employeeId`, `planYearId`, `submittedAt`, `claimStatus`, `totalAmountSubmitted`.

### Integrity constraints
- `totalAmountSubmitted` should reconcile to sum(`ClaimExpense.amountSubmitted`).
- `totalAmountApproved` should reconcile to adjudication outcomes in `ReviewDecision`.
- Reconciliation jobs should update `lastRecomputedAt` and emit audit events on drift.

### Sensitive fields
Contains PHI/financial information by association.

### Retention considerations
Typically 7+ years; maintain immutable audit trail.

### Example JSON object
```json
{
  "claimId": "clm_778901",
  "employeeId": "emp_100245",
  "planYearId": "py_2026",
  "submittedAt": "2026-02-05T13:11:55Z",
  "claimStatus": "IN_REVIEW",
  "totalAmountSubmitted": 325.4,
  "totalAmountApproved": 0.0,
  "channel": "WEB"
}
```

---

## 8) ClaimExpense

### Purpose
Line-item detail for each service or product being claimed.

### Key fields
- `claimExpenseId`
- `claimId`
- `recipientId`
- `serviceDate`
- `providerName`
- `expenseType`
- `amountSubmitted`
- `amountEligible`
- `diagnosisOrProcedureCode` (optional, encrypted, policy-gated)
- `diagnosisCodeAccessReason` (required when code is viewed/edited)

### Relationships
- Many ClaimExpenses belong to one Claim.
- Each ClaimExpense references one EligibleRecipient.

### Required fields
`claimExpenseId`, `claimId`, `recipientId`, `serviceDate`, `expenseType`, `amountSubmitted`.

### Sensitive fields
High PHI risk (service date/provider/procedure).

### Retention considerations
Protected health information retention; strict access and purge policies consistent with legal requirements.

### Example JSON object
```json
{
  "claimExpenseId": "ce_1001",
  "claimId": "clm_778901",
  "recipientId": "rec_553",
  "serviceDate": "2026-01-18",
  "providerName": "Downtown Pediatrics",
  "expenseType": "COPAY",
  "amountSubmitted": 45.0,
  "amountEligible": null,
  "diagnosisOrProcedureCode": null
}
```

---

## 9) Document

### Purpose
Stores metadata for uploaded evidence (receipts, EOBs, letters), with pointer to secure object storage.

### Key fields
- `documentId`
- `documentHandle` (opaque lookup token)
- `storageLocatorRef` (internal resolver key, not exposed externally)
- `fileName`
- `mimeType`
- `storageUri`
- `sha256`
- `uploadedBy`
- `uploadedAt`
- `documentStatus`

### Relationships
- Many Documents attach through typed `DocumentLink` records for Claim, Appeal, or MissingInformationRequest ownership.

### Required fields
`documentId`, `documentHandle`, `uploadedAt`, `uploadedBy`.

### Sensitive fields
The file content is highly sensitive; hashes and URIs are sensitive operational data.

### Retention considerations
Apply records-retention schedule with legal hold and defensible deletion.

### Example JSON object
```json
{
  "documentId": "doc_90011",
  "documentHandle": "dhl_8f7d21",
  "storageLocatorRef": "docloc_prod_2026_02_90011",
  "fileName": "receipt_jan18.pdf",
  "mimeType": "application/pdf",
  "storageUri": null,
  "sha256": "f92d38c8a2b5...",
  "uploadedBy": "emp_100245",
  "uploadedAt": "2026-02-05T13:09:21Z",
  "documentStatus": "ACTIVE"
}
```

---

## 10) ReviewTask

### Purpose
Operational work item for claim/manual adjudication queues.

### Key fields
- `reviewTaskId`
- `claimId`
- `queueName`
- `assignedTo`
- `priority`
- `taskStatus` (OPEN, IN_PROGRESS, BLOCKED, COMPLETED)
- `dueAt`
- `createdAt`

### Relationships
- Many ReviewTasks may exist for one Claim.
- One ReviewTask may produce one or more ReviewDecisions.

### Required fields
`reviewTaskId`, `claimId`, `queueName`, `taskStatus`, `createdAt`.

### Sensitive fields
Contains references to sensitive claims; assignment data may be internal-sensitive.

### Retention considerations
Retain with claim audit history.

### Example JSON object
```json
{
  "reviewTaskId": "rt_6003",
  "claimId": "clm_778901",
  "queueName": "medical_receipt_validation",
  "assignedTo": "usr_reviewer_21",
  "priority": "HIGH",
  "taskStatus": "IN_PROGRESS",
  "dueAt": "2026-02-07T23:59:59Z",
  "createdAt": "2026-02-05T13:12:01Z"
}
```

---

## 11) ReviewDecision

### Purpose
Captures adjudication outcomes at claim or line-item level.

### Key fields
- `reviewDecisionId`
- `claimId`
- `claimExpenseId` (nullable for claim-level decisions)
- `decision` (APPROVE, PARTIAL_APPROVE, DENY, REQUEST_INFO)
- `approvedAmount`
- `denialReasonCode` (nullable, legacy single-code compatibility field)
- `reviewTaskId` (nullable)
- `supersedesDecisionId` (nullable self-reference)
- `decisionBy`
- `decisionAt`
- `notes`

### Relationships
- Many ReviewDecisions belong to one Claim.
- Optional link to one ReviewTask for explicit task-to-decision lineage.
- May supersede a prior ReviewDecision during rework cycles.
- Many-to-many denial coding through `ReviewDecisionDenialReason`.
- May trigger MissingInformationRequest and typed Notification links.

### Required fields
`reviewDecisionId`, `claimId`, `decision`, `decisionBy`, `decisionAt`.

### Sensitive fields
Contains medical/financial rationale notes.

### Retention considerations
Core adjudication evidence; immutable and retained long-term.

### Example JSON object
```json
{
  "reviewDecisionId": "rd_7991",
  "claimId": "clm_778901",
  "claimExpenseId": "ce_1001",
  "decision": "REQUEST_INFO",
  "approvedAmount": 0.0,
  "denialReasonCode": null,
  "decisionBy": "usr_reviewer_21",
  "decisionAt": "2026-02-06T16:42:18Z",
  "notes": "Need itemized receipt with provider tax ID"
}
```

---

## 12) DenialReason

### Purpose
Standardized catalog of denial codes and policy-based explanations.

### Key fields
- `denialReasonCode`
- `title`
- `description`
- `regulatoryReference`
- `activeFlag`

### Relationships
- One DenialReason can be referenced by many ReviewDecisions.

### Required fields
`denialReasonCode`, `title`, `activeFlag`.

### Sensitive fields
None (reference data).

### Retention considerations
Keep full historical catalog; do not delete codes once used.

### Example JSON object
```json
{
  "denialReasonCode": "DR-ELIG-001",
  "title": "Expense not eligible",
  "description": "Submitted expense type is not eligible under plan rules.",
  "regulatoryReference": "IRS Pub 502",
  "activeFlag": true
}
```

---

## 13) MissingInformationRequest

### Purpose
Tracks formal requests for additional employee documentation/information.

### Key fields
- `requestId`
- `claimId`
- `requestedAt`
- `dueAt`
- `requestReason`
- `requestStatus` (OPEN, RESPONDED, OVERDUE, CLOSED)
- `responseReceivedAt`

### Relationships
- Many requests can exist for one Claim.
- One request can have many Documents.

### Required fields
`requestId`, `claimId`, `requestedAt`, `dueAt`, `requestStatus`.

### Sensitive fields
Contains PHI-related request details.

### Retention considerations
Retain with claim record and correspondence evidence.

### Example JSON object
```json
{
  "requestId": "mir_302",
  "claimId": "clm_778901",
  "requestedAt": "2026-02-06T16:45:00Z",
  "dueAt": "2026-02-20T23:59:59Z",
  "requestReason": "Please provide EOB showing patient responsibility amount.",
  "requestStatus": "OPEN",
  "responseReceivedAt": null
}
```

---

## 14) Appeal

### Purpose
Represents a member appeal against a denial/partial decision.

### Key fields
- `appealId`
- `claimId`
- `employeeId`
- `appealedReviewDecisionId` (nullable direct link for simple flows)
- `filedAt`
- `appealStatus` (FILED, UNDER_REVIEW, UPHELD, OVERTURNED, CLOSED)
- `appealReason`
- `resolutionSummary`
- `resolvedAt`

### Relationships
- Many Appeals may reference one Claim.
- Appeals should link to one or more challenged decisions via `AppealDecisionLink`.
- One Appeal has many Documents and Notifications.

### Required fields
`appealId`, `claimId`, `employeeId`, `filedAt`, `appealStatus`.

### Sensitive fields
May contain medical details and legal correspondence.

### Retention considerations
Retain for dispute resolution and legal defense timeline.

### Example JSON object
```json
{
  "appealId": "apl_8821",
  "claimId": "clm_778901",
  "employeeId": "emp_100245",
  "filedAt": "2026-03-01T12:00:00Z",
  "appealStatus": "UNDER_REVIEW",
  "appealReason": "Receipt was originally unreadable; clearer copy attached.",
  "resolutionSummary": null,
  "resolvedAt": null
}
```

---

## 15) PaymentBatch

### Purpose
Represents a disbursement run to pay approved reimbursements.

### Key fields
- `paymentBatchId`
- `planYearId`
- `batchDate`
- `paymentMethod` (ACH, CHECK)
- `batchStatus` (DRAFT, SUBMITTED, SETTLED, FAILED)
- `totalAmount`
- `lineCount`
- `settledAt`

### Relationships
- One PaymentBatch has many PaymentBatchLines.

### Required fields
`paymentBatchId`, `batchDate`, `paymentMethod`, `batchStatus`, `totalAmount`.

### Sensitive fields
Financial transfer metadata.

### Retention considerations
Financial records usually retained 7+ years minimum.

### Example JSON object
```json
{
  "paymentBatchId": "pb_2026_0212_01",
  "planYearId": "py_2026",
  "batchDate": "2026-02-12",
  "paymentMethod": "ACH",
  "batchStatus": "SUBMITTED",
  "totalAmount": 128433.22,
  "lineCount": 482,
  "settledAt": null
}
```

---

## 16) PaymentBatchLine

### Purpose
Line-level payment instruction for a specific approved claim (or portion).

### Key fields
- `paymentBatchLineId`
- `paymentBatchId`
- `claimId`
- `employeeId`
- `reviewDecisionId` (adjudication basis for payable amount)
- `amount`
- `paymentStatus` (PENDING, SENT, SETTLED, RETURNED)
- `traceNumber`
- `paidAt`

### Relationships
- Many PaymentBatchLines belong to one PaymentBatch.
- Many lines may map to one Claim (split/adjustments).

### Required fields
`paymentBatchLineId`, `paymentBatchId`, `claimId`, `employeeId`, `amount`, `paymentStatus`.

### Sensitive fields
Banking/payment routing artifacts.

### Retention considerations
Financial transaction record retention with reconciliation history.

### Example JSON object
```json
{
  "paymentBatchLineId": "pbl_99102",
  "paymentBatchId": "pb_2026_0212_01",
  "claimId": "clm_778901",
  "employeeId": "emp_100245",
  "amount": 45.0,
  "paymentStatus": "SENT",
  "traceNumber": "ACH-20260212-44771",
  "paidAt": "2026-02-12T20:10:00Z"
}
```

---

## 17) Notification

### Purpose
Outbound communication log for employee/admin messages (email/SMS/portal).

### Key fields
- `notificationId`
- `employeeId`
- `templateVariables` (tokenized map with sensitivity tags)
- `containsSensitiveData`
- `channel` (EMAIL, SMS, PORTAL)
- `templateCode`
- `deliveryStatus` (QUEUED, SENT, DELIVERED, FAILED)
- `sentAt`

### Relationships
- Notifications should reference domain records through typed link tables (e.g., `ClaimNotification`, `AppealNotification`).

### Required fields
`notificationId`, `employeeId`, `channel`, `templateCode`, `deliveryStatus`.

### Sensitive fields
Message payload may contain claim and PII details.

### Retention considerations
Keep enough for compliance and dispute support; purge/redact payloads per privacy policy.

### Example JSON object
```json
{
  "notificationId": "ntf_57119",
  "employeeId": "emp_100245",
  "templateVariables": {
    "requestId": "mir_302",
    "dueDate": "2026-02-20",
    "sensitivity": "PHI_MINIMIZED"
  },
  "containsSensitiveData": true,
  "channel": "EMAIL",
  "templateCode": "MIR_OPEN_V2",
  "deliveryStatus": "DELIVERED",
  "sentAt": "2026-02-06T16:46:03Z"
}
```

---

## 18) AuditEvent

### Purpose
Tamper-evident event log of user/system actions for security and compliance.

### Key fields
- `auditEventId`
- `occurredAt`
- `actorType` (EMPLOYEE, ADMIN, SYSTEM)
- `actorId`
- `action`
- `entityType`, `entityId`
- `ipAddress`
- `userAgent`
- `beforeHash`, `afterHash`
- `redactionLevel`

### Relationships
- References nearly all mutable domain entities.

### Required fields
`auditEventId`, `occurredAt`, `actorType`, `action`, `entityType`, `entityId`.

### Sensitive fields
IP/user-agent and potentially captured state deltas.

### Retention considerations
Long retention with WORM controls recommended.

### Example JSON object
```json
{
  "auditEventId": "aud_20260206_771",
  "occurredAt": "2026-02-06T16:42:18Z",
  "actorType": "ADMIN",
  "actorId": "usr_reviewer_21",
  "action": "REVIEW_DECISION_CREATED",
  "entityType": "ReviewDecision",
  "entityId": "rd_7991",
  "ipAddress": "10.14.9.21",
  "userAgent": "Mozilla/5.0",
  "beforeHash": "a1c2...",
  "afterHash": "bc33..."
}
```

---

## 19) ExportJob

### Purpose
Tracks data extracts/feeds to payroll, finance, BI, regulators, or archival systems.

### Key fields
- `exportJobId`
- `agencyId`
- `jobType`
- `periodStart`, `periodEnd`
- `requestedBy`
- `status` (QUEUED, RUNNING, SUCCEEDED, FAILED)
- `recordCount`
- `outputUri`
- `asOfTimestamp`
- `sourceQueryHash`
- `schemaVersion`
- `replayKey`
- `startedAt`, `finishedAt`

### Relationships
- Often references one Agency and includes snapshots of Claims/Payments/Enrollments.

### Required fields
`exportJobId`, `jobType`, `status`, `requestedBy`, `startedAt`.

### Sensitive fields
Export files often contain PII/PHI/financial data.

### Retention considerations
Retain job metadata long-term; output files per data-sharing agreements.

### Example JSON object
```json
{
  "exportJobId": "exp_2026_02_15_01",
  "agencyId": "agency_DOE",
  "jobType": "PAYROLL_RECONCILIATION",
  "periodStart": "2026-02-01",
  "periodEnd": "2026-02-14",
  "requestedBy": "usr_fin_ops_3",
  "status": "SUCCEEDED",
  "recordCount": 1442,
  "outputUri": "s3://hcfsa-exports/prod/exp_2026_02_15_01.csv.gpg",
  "startedAt": "2026-02-15T01:00:00Z",
  "finishedAt": "2026-02-15T01:12:44Z"
}
```

---

## 20) AdminConfiguration

### Purpose
Stores tenant/global policy parameters, feature toggles, and operational settings.

### Key fields
- `configId`
- `scope` (GLOBAL, AGENCY, PLAN_YEAR)
- `scopeId`
- `precedence`
- `isOverride`
- `configKey`
- `configValue` (JSON)
- `effectiveFrom`, `effectiveTo`
- `updatedBy`, `updatedAt`

### Relationships
- May apply to Agency, PlanYear, or platform-wide behavior.

### Required fields
`configId`, `scope`, `configKey`, `configValue`, `effectiveFrom`, `updatedAt`.

### Sensitive fields
May include security/threshold settings (sensitive operational data).

### Retention considerations
Version every change and retain historical values for reproducibility/audit.

### Example JSON object
```json
{
  "configId": "cfg_1200",
  "scope": "PLAN_YEAR",
  "scopeId": "py_2026",
  "configKey": "claim.autoApprove.maxAmount",
  "configValue": {
    "currency": "USD",
    "amount": 50
  },
  "effectiveFrom": "2026-01-01T00:00:00Z",
  "effectiveTo": null,
  "updatedBy": "usr_sysadmin_1",
  "updatedAt": "2025-12-20T13:14:00Z"
}
```

---

## System of Record vs Derived/Imported Classification

### Likely Systems of Record (SoR) inside HCFSA platform
- Enrollment
- ContributionElection
- Claim
- ClaimExpense
- ReviewTask
- ReviewDecision
- MissingInformationRequest
- Appeal
- PaymentBatch
- PaymentBatchLine
- Notification (delivery log)
- AuditEvent
- AdminConfiguration
- Document metadata (not binary object store itself)

### Likely Imported from External Systems (authoritative elsewhere)
- Employee (usually HRIS/payroll is primary)
- Agency (enterprise master data)
- DenialReason (may be maintained internally or imported from policy governance source)
- PlanYear (may be configured internally, but often initialized from benefits policy/HR source)

### Likely Derived / Computed / Replicated
- ExportJob (operational metadata about derived extracts)
- Computed claim balances and available funds (derived from elections, payroll contributions, and paid claims)
- Aggregated status fields (e.g., claim-level status derived from line-level decisions)

## Recommended Implementation Patterns

- Use immutable event/versioning for elections, decisions, and payments.
- Separate **document metadata** (DB) from **binary content** (encrypted object storage).
- Introduce consistent IDs (`emp_*`, `clm_*`, etc.) for observability.
- Track `createdAt/updatedAt` and `createdBy/updatedBy` on all mutable entities.
- Add soft-delete flags only where legally permissible; prefer archival states to deletion.


---

## 21) ContributionPosting

### Purpose
Immutable ledger entry representing actual payroll contribution funding activity.

### Key fields
- `contributionPostingId`
- `enrollmentId`
- `employeeId`
- `planYearId`
- `payDate`
- `amount`
- `postingType` (CREATE, ADJUST, REVERSE)
- `sourcePayrollRunId`
- `reversalOfPostingId` (nullable)
- `sequenceNumber`
- `effectiveAt`

### Relationships
- Many ContributionPostings belong to one Enrollment.
- Contribution postings feed AccountBalanceSnapshot and export deltas.

## 22) AccountBalanceSnapshot

### Purpose
Materialized read model of available/committed balance by employee and plan year.

### Key fields
- `snapshotId`
- `employeeId`
- `planYearId`
- `asOfTimestamp`
- `availableBalance`
- `committedAmount`
- `paidAmount`
- `reconciliationStatus`

## 23) ReviewDecisionDenialReason

### Purpose
Associative entity for multi-reason denials and member-safe wording.

### Key fields
- `reviewDecisionId`
- `denialReasonCode`
- `rankOrder`
- `memberVisibleExplanation`

## 24) AppealDecisionLink

### Purpose
Links an appeal to one or many specific review decisions being challenged.

### Key fields
- `appealDecisionLinkId`
- `appealId`
- `reviewDecisionId`
- `linkType` (PRIMARY, RELATED)

## 25) DocumentLink

### Purpose
Typed ownership junction for compliance-grade referential integrity.

### Key fields
- `documentLinkId`
- `documentId`
- `claimId` (nullable)
- `appealId` (nullable)
- `missingInformationRequestId` (nullable)
- `linkType`

## 26) LegalHold

### Purpose
Suspends purge/deletion for linked records under litigation, audit, or investigation.

### Key fields
- `legalHoldId`
- `holdReason`
- `status` (ACTIVE, RELEASED)
- `appliesToEntityType`
- `appliesToEntityId`
- `placedAt`
- `releasedAt`

## 27) ExternalIdMapping

### Purpose
Tracks stable identifiers required by downstream payroll/finance/regulatory consumers.

### Key fields
- `externalIdMappingId`
- `entityType`
- `entityId`
- `targetSystem`
- `externalReference`
- `effectiveFrom`
- `effectiveTo`

## 28) ExportContractVersion

### Purpose
Versioned export contract registry with compatibility policy metadata.

### Key fields
- `exportContractVersionId`
- `jobType`
- `schemaVersion`
- `compatibilityMode`
- `encodingProfile`
- `decimalFormatProfile`
- `activeFrom`
