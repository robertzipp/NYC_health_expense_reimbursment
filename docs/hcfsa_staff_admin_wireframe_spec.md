# HCFSA Staff-Facing Admin and Review Text Wireframe Specifications

## 1) Reviewer Queue

### Purpose
Provide adjudicators a prioritized list of claims requiring review and action.

### User role
Claims Reviewer / Benefits Adjudicator

### Fields
- Queue name (new, aged, appeals, SLA-risk)
- Claim ID
- Employee ID / name
- Date received
- Total amount claimed
- Current status
- SLA due date / aging days
- Flags (missing docs, high-dollar, duplicate risk)
- Last touch user/time

### Actions
- Open claim detail
- Reassign claim
- Claim batch select
- Put on hold
- Mark for supervisor review

### Filters
- Status
- Received date range
- Aging bucket
- Amount range
- Plan year
- Reviewer assignment
- Flag type

### Decision points
- Is claim within reviewer authority thresholds?
- Is SLA at risk requiring immediate action?
- Is claim complete enough for adjudication?

### Audit events
- Queue viewed
- Filter set changed
- Claim opened from queue
- Claim reassigned
- Claim hold applied/removed

### Error states
- Queue load failure
- Stale queue data warning
- Reassignment conflict (claim already locked)

---

## 2) Claim Detail

### Purpose
Present full claim context and line-item data for adjudication decisions.

### User role
Claims Reviewer / Supervisor

### Fields
- Claim header (ID, employee, plan, submission date)
- Eligibility snapshot at service date
- Expense line items (date, category, amount, recipient)
- Prior claim history summary
- Notes and correspondence log
- System rule results
- Recommended adjudication outcome

### Actions
- Approve all
- Partially approve
- Deny
- Request missing information
- Add internal note
- Escalate to supervisor

### Filters
- Line-item status
- Expense category
- Rule outcome (pass/fail/manual review)

### Decision points
- Are expenses eligible under plan and IRS rules?
- Is documentation sufficient and authentic?
- Are duplicate or out-of-window expenses present?

### Audit events
- Claim opened
- Claim lock acquired/released
- Note added/edited
- Decision prepared
- Decision submitted

### Error states
- Claim lock unavailable
- Rule engine response timeout
- Save decision draft failure

---

## 3) Document Viewer

### Purpose
Enable review of uploaded receipts/EOBs and extraction of key evidence.

### User role
Claims Reviewer / Appeals Analyst

### Fields
- Document list with metadata
- Preview pane
- OCR extracted fields
- Confidence indicators
- Document-to-line-item linkage
- Annotation layer (internal only)

### Actions
- Zoom/rotate/download
- Link/unlink doc to expense line
- Flag suspicious document
- Add annotation
- Request replacement document

### Filters
- Document type
- Linked/unlinked status
- OCR confidence threshold
- Upload date

### Decision points
- Does document prove date, amount, provider, and recipient?
- Is itemization adequate for category?
- Is OCR mismatch material to decision?

### Audit events
- Document viewed/downloaded
- Linkage changed
- Suspicion flag set/cleared
- Annotation created/deleted

### Error states
- File render failure
- OCR service unavailable
- Corrupted or unsupported document

---

## 4) Request Missing Information

### Purpose
Issue structured follow-up requests for claim deficiencies.

### User role
Claims Reviewer

### Fields
- Request template selector
- Custom request message
- Missing item checklist
- Response due date
- Communication channel
- Referenced line items

### Actions
- Send request
- Save draft request
- Preview message
- Cancel request flow

### Filters
- Template category
- Due date preset
- Communication preference

### Decision points
- Is missing information resolvable without denial?
- Is request specific enough to avoid repeat outreach?
- Is due date compliant with policy timelines?

### Audit events
- Missing-info draft created
- Request sent
- Due date updated
- Request canceled

### Error states
- Notification delivery failure
- Template service unavailable
- Policy deadline violation block

---

## 5) Approve Claim

### Purpose
Finalize full approval for eligible claim lines and trigger payment eligibility.

### User role
Claims Reviewer

### Fields
- Claim total approved amount
- Per-line approval status
- Payment method on file
- Effective approval timestamp
- Reviewer attestation

### Actions
- Confirm approval
- Edit approval rationale
- Return to claim detail

### Filters
- Not applicable (single decision screen)

### Decision points
- Are all lines fully eligible?
- Does approved amount match evidence and limits?
- Is secondary review required by threshold?

### Audit events
- Approval initiated
- Approval confirmed
- Override reason recorded
- Payment-ready event emitted

### Error states
- Approval submission failed
- Post-decision payment trigger failure
- Concurrent update conflict

---

## 6) Partially Approve Claim

### Purpose
Approve eligible portions while denying or pend-ing ineligible lines.

### User role
Claims Reviewer / Supervisor

### Fields
- Line-by-line decision table
- Approved amount per line
- Denial reason per non-approved line
- Total approved vs denied summary
- Member-facing explanation preview

### Actions
- Set line outcome
- Apply bulk reason code
- Validate totals
- Confirm partial approval

### Filters
- Eligible/ineligible/needs info line states
- Amount variance flags

### Decision points
- Which lines meet eligibility criteria?
- Are reason codes accurate and complete?
- Does partial determination require supervisor signoff?

### Audit events
- Line outcome changed
- Reason code assigned
- Partial decision saved
- Partial approval finalized

### Error states
- Totals mismatch block
- Missing reason code block
- Decision persistence error

---

## 7) Deny Claim

### Purpose
Record denial determination with policy-grounded rationale.

### User role
Claims Reviewer / Supervisor

### Fields
- Denial reason code(s)
- Narrative rationale
- Policy reference links
- Appeal eligibility flag
- Appeal deadline date
- Determination letter preview

### Actions
- Confirm denial
- Save draft denial
- Escalate for QA review

### Filters
- Reason code categories
- Appeal-eligible only toggle

### Decision points
- Is denial complete, defensible, and policy aligned?
- Must claim be reopened for clarification instead?
- Is appeal window correctly calculated?

### Audit events
- Denial drafted
- Denial finalized
- Determination letter generated
- Appeal clock started

### Error states
- Letter generation failure
- Missing mandatory reason code
- Deadline computation error

---

## 8) Appeal Review

### Purpose
Support independent review of appealed determinations.

### User role
Appeals Analyst / Supervisor

### Fields
- Original determination summary
- Appeal submission details
- New evidence list
- Applicable policy and precedents
- Recommendation panel
- Final appeal outcome

### Actions
- Uphold denial
- Overturn denial
- Modify decision
- Request additional appeal evidence
- Assign peer review

### Filters
- Appeal age/SLA
- Outcome recommendation
- Evidence completeness
- Analyst assignment

### Decision points
- Does new evidence materially change eligibility?
- Was original adjudication procedurally correct?
- Is external compliance/legal review required?

### Audit events
- Appeal opened
- Evidence reviewed markers
- Outcome draft saved
- Final appeal disposition issued

### Error states
- Appeal package retrieval failure
- Precedent service unavailable
- Finalization conflict

---

## 9) Payment Batch Creation

### Purpose
Group approved claims into disbursement batches with controls and reconciliation.

### User role
Payment Operations Specialist

### Fields
- Batch ID
- Payment cycle date
- Included claims count
- Total disbursement amount
- Funding account
- Payment method breakdown
- Reconciliation status

### Actions
- Generate draft batch
- Exclude/include claims
- Validate funding totals
- Submit batch for release
- Export NACHA/ACH file

### Filters
- Approval date range
- Payment method
- Plan year
- Batch status

### Decision points
- Are all claims payment-eligible and non-duplicative?
- Does batch pass funding and fraud checks?
- Is dual-control approval required before release?

### Audit events
- Batch generated
- Claim added/removed from batch
- Batch approved/rejected
- Payment file exported
- Batch released

### Error states
- Funding mismatch
- Duplicate payment detection halt
- Bank file generation error

---

## 10) Export Center

### Purpose
Provide governed exports for operational, audit, and compliance needs.

### User role
Operations Analyst / Compliance Officer / Admin

### Fields
- Export type
- Data scope (claims, appeals, payments, receipts)
- Date range
- Format (CSV, XLSX)
- PII masking level
- Request status/history

### Actions
- Create export request
- Download completed export
- Cancel pending export
- Clone prior export

### Filters
- Export status
- Requestor
- Data domain
- Date created

### Decision points
- Does requestor have permission for selected data scope?
- Is masking level appropriate for recipient?
- Should export be asynchronous due to size?

### Audit events
- Export requested
- Permission check outcome
- Export completed
- Export downloaded
- Export canceled

### Error states
- Authorization failure
- Export job timeout
- File unavailable/expired

---

## 11) Reports Dashboard

### Purpose
Show operational KPIs, quality trends, and compliance indicators.

### User role
Manager / Operations Lead / Compliance

### Fields
- KPI cards (volume, turnaround, approval rate, denial rate)
- Trend charts
- SLA breach counts
- Top denial reasons
- Appeal overturn rate
- Drill-down tables

### Actions
- Change report period
- Drill into metric
- Save view
- Share snapshot
- Export report

### Filters
- Date range
- Plan year
- Team/reviewer
- Claim type/category
- Employer group

### Decision points
- Are SLAs being met?
- Do denial patterns indicate training/config issues?
- Are appeal outcomes signaling policy misapplication?

### Audit events
- Dashboard viewed
- Filter set applied
- Report exported/shared
- Saved view created/updated

### Error states
- Metrics service partial outage
- Data freshness warning
- Visualization render failure

---

## 12) Admin Configuration

### Purpose
Manage plan rules, decision logic settings, templates, and role access.

### User role
System Administrator / Product Operations Admin

### Fields
- Plan-year configuration
- Eligibility rules toggles
- Reason code catalog
- Missing-info templates
- SLA thresholds
- User roles and permissions
- Feature flag controls
- Change effective dates

### Actions
- Create/update configuration
- Publish changes
- Roll back version
- Simulate rule impact
- Assign/revoke roles

### Filters
- Configuration domain
- Effective date
- Environment (if applicable)
- Last modified by

### Decision points
- Is change compliant with policy and legal requirements?
- Should change be immediate or scheduled?
- Is two-person approval required for sensitive updates?

### Audit events
- Config draft created/edited
- Publish approved/rejected
- Version rollback executed
- Permission change applied
- Rule simulation run

### Error states
- Publish validation failure
- Version conflict detected
- Unauthorized modification attempt
- Downstream propagation failure
