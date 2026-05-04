# HCFSA Business Rules Catalog

This catalog defines baseline business rules for the HCFSA platform. Each rule is written for implementation, operations, support, and audit alignment.

## BR-001 — Plan Year
- **Plain-language rule:** Participants can incur eligible HCFSA expenses only during the active plan year.
- **System behavior:**
  - Validate each claim’s date of service against the participant’s plan year start/end dates.
  - Reject claims with service dates outside the plan year unless covered by a configured grace period rule.
  - Show plan-year boundaries on dashboard and claim-entry screens.
- **Configurable or hard-coded?** Configurable (plan-year calendar by employer group).
- **Data needed:** Employer group ID, plan-year start date, plan-year end date, claim service date, participant enrollment dates.
- **Error message or user-facing explanation:** “This expense date is outside your plan year. Please submit expenses dated within your eligible period.”
- **Edge cases:** Mid-year employer plan changes; retroactive eligibility corrections; claim crossing year boundary with multiple line items.

## BR-002 — Grace Period
- **Plain-language rule:** If enabled, participants may incur new expenses for a limited period after plan year end.
- **System behavior:**
  - Apply grace-period window only for plans with grace period enabled.
  - Include grace-period claims against prior plan year balance.
  - Prevent overlap conflicts where carryover and grace-period designs are mutually exclusive (if policy requires).
- **Configurable or hard-coded?** Configurable (enabled flag + number of days/months).
- **Data needed:** Plan grace-period setting, grace-period duration, plan-year end date, claim service date.
- **Error message or user-facing explanation:** “Your plan’s grace period has ended for this plan year.”
- **Edge cases:** Leap-year date math; employer-specific exception approvals; grace period disabled after open enrollment.

## BR-003 — Claims Run-Out Period
- **Plain-language rule:** Participants may submit claims for prior-year eligible expenses until the run-out deadline.
- **System behavior:**
  - Accept submissions only through run-out end date/time.
  - Lock upload and claim creation actions after cutoff.
  - Keep read-only access to historical claims after run-out expires.
- **Configurable or hard-coded?** Configurable (run-out duration and exact cutoff timestamp).
- **Data needed:** Plan-year end date, run-out length, platform timezone, claim submission timestamp, claim service date.
- **Error message or user-facing explanation:** “The claim filing deadline for this plan year has passed.”
- **Edge cases:** Timezone disputes near midnight; delayed mail/fax ingestion; outage during final submission day.

## BR-004 — Minimum Claim Submission Threshold
- **Plain-language rule:** Claims below the minimum allowed amount cannot be submitted unless they exhaust the remaining balance.
- **System behavior:**
  - Validate total claim amount against configured minimum threshold.
  - Allow exception when remaining available balance is below the threshold and claim equals remaining balance.
- **Configurable or hard-coded?** Configurable (currency amount by plan).
- **Data needed:** Claim total amount, participant available balance, plan minimum threshold.
- **Error message or user-facing explanation:** “Minimum claim amount is $X.XX unless you are claiming your remaining balance in full.”
- **Edge cases:** Currency rounding (cents); split claims submitted same day; adjusted claims after partial denial.

## BR-005 — Eligible Recipients
- **Plain-language rule:** Expenses are reimbursable only for eligible individuals tied to the participant’s account.
- **System behavior:**
  - Validate recipient relationship and eligibility period (employee, spouse, tax dependent where permitted).
  - Block reimbursement for non-eligible individuals.
  - Require dependent profile before claim submission when recipient is not employee.
- **Configurable or hard-coded?** Hybrid (core IRS-driven logic hard-coded; relationship options configurable by plan UI policy).
- **Data needed:** Participant profile, dependent records, relationship type, dependent DOB, eligibility effective/termination dates, claim recipient.
- **Error message or user-facing explanation:** “This recipient is not eligible under your HCFSA account.”
- **Edge cases:** Dependent aging out mid-year; custody/tax-dependent status changes; retroactive dependent additions.

## BR-006 — Eligible Expense Documentation
- **Plain-language rule:** Every non-auto-substantiated claim must include documentation proving date, amount, and service details.
- **System behavior:**
  - Require document upload (or external feed evidence) before claim can move to adjudication.
  - Validate required fields via OCR/manual review checklist.
  - Route incomplete documentation claims to denied/pended status based on workflow policy.
- **Configurable or hard-coded?** Hybrid (required evidence attributes hard-coded; workflow thresholds configurable).
- **Data needed:** Claim type, substantiation source, document images/PDF, extracted merchant/provider, service date, amount, description.
- **Error message or user-facing explanation:** “We need an itemized receipt or EOB showing provider, date of service, and amount.”
- **Edge cases:** Blurry uploads; combined household receipts with mixed eligible/ineligible items; duplicate doc reused for multiple claims.

## BR-007 — OTC Documentation
- **Plain-language rule:** OTC expenses must include itemized proof and, where applicable, prescription evidence per current policy.
- **System behavior:**
  - Classify OTC claims using merchant category + item metadata.
  - Enforce additional documentation fields when OTC category requires it.
  - Deny or pend OTC claims with missing required details.
- **Configurable or hard-coded?** Hybrid (OTC eligibility list configurable via policy table; mandatory fields rule-based/hard-coded).
- **Data needed:** Itemized receipt lines, SKU/item name, OTC category mapping, prescription indicator (if required), purchase date, amount.
- **Error message or user-facing explanation:** “Your OTC claim needs itemized documentation and any required prescription information.”
- **Edge cases:** Retail receipt abbreviations; bundled purchases; policy changes effective mid-year.

## BR-008 — Contribution Minimums and Maximums
- **Plain-language rule:** Elections must be within plan minimum and legal/plan maximum limits.
- **System behavior:**
  - Validate election amount during enrollment and when changes are permitted.
  - Enforce statutory maximum cap and employer-level cap (lowest wins).
  - Reject payroll contribution schedules that would exceed annual election.
- **Configurable or hard-coded?** Hybrid (statutory cap configurable annually from compliance table; plan min/max configurable).
- **Data needed:** Election amount, plan min/max, compliance-year statutory cap, payroll frequency, remaining contribution schedule.
- **Error message or user-facing explanation:** “Your election must be between $X and $Y for this plan year.”
- **Edge cases:** Mid-year hire proration policy; cap updates for new tax year; payroll calendar anomalies (27th paycheck year).

## BR-009 — New Employee Enrollment Window
- **Plain-language rule:** Newly eligible employees must enroll within a fixed window after eligibility start.
- **System behavior:**
  - Open enrollment task at eligibility effective date.
  - Auto-close window at configured deadline.
  - Require qualifying-life-event workflow after deadline.
- **Configurable or hard-coded?** Configurable (number of days; trigger event).
- **Data needed:** Employment start date, benefits eligibility date, enrollment window length, submission timestamp.
- **Error message or user-facing explanation:** “Your new-hire enrollment window has closed. You may enroll only with a qualifying event.”
- **Edge cases:** Delayed HRIS feed; rehires; weekend/holiday deadline extension policy.

## BR-010 — Annual Re-Enrollment
- **Plain-language rule:** Participants must actively elect each plan year unless employer policy enables auto-reenrollment.
- **System behavior:**
  - Prompt annual election during open enrollment.
  - If no election by close, apply employer policy: default to $0 or configured carry-forward election.
  - Produce confirmation notice of final election status.
- **Configurable or hard-coded?** Configurable (reenrollment required flag, default behavior).
- **Data needed:** Open enrollment window dates, prior-year election, participant submission status, employer reenrollment policy.
- **Error message or user-facing explanation:** “Open enrollment ended without an election; your plan year contribution is set per employer policy.”
- **Edge cases:** Late approved exceptions; merged employer groups with different policies; plan migration year.

## BR-011 — Denial Reasons
- **Plain-language rule:** Every denied claim must map to a standardized denial reason code and clear explanation.
- **System behavior:**
  - Require reason code selection before final denial status.
  - Attach human-readable explanation template by code.
  - Expose denial rationale in participant portal, email, and CSR tooling.
- **Configurable or hard-coded?** Configurable (reason code catalog and templates, with protected system codes).
- **Data needed:** Claim adjudication findings, denial reason code table, communication template mapping.
- **Error message or user-facing explanation:** “Claim denied: [Reason]. Review details and appeal by the listed deadline if applicable.”
- **Edge cases:** Multiple denial causes for one claim; partial line-item denial; code deprecation/audit traceability.

## BR-012 — Appeal Deadlines
- **Plain-language rule:** Appeals must be received within the required timeframe from denial notice date.
- **System behavior:**
  - Compute appeal deadline from denial notification date using plan/compliance rules.
  - Reject late appeals unless admin override authorization is recorded.
  - Show countdown and final date in claimant communications.
- **Configurable or hard-coded?** Configurable (deadline duration and calendar-day/business-day method).
- **Data needed:** Denial notice timestamp, appeal policy duration, holiday calendar (if business-day method), appeal submission timestamp.
- **Error message or user-facing explanation:** “The appeal deadline has passed for this claim.”
- **Edge cases:** Notification delivery failure; timezone near-deadline submissions; reopened claims resetting appeal clock.

## BR-013 — Monthly Processing Cutoffs
- **Plain-language rule:** Claims approved after the monthly cutoff roll into the next processing cycle.
- **System behavior:**
  - Determine cycle assignment based on approval timestamp and cutoff calendar.
  - Display expected reimbursement cycle date in claim status.
  - Support employer-specific cutoff schedules.
- **Configurable or hard-coded?** Configurable (cutoff day/time and timezone by employer/program).
- **Data needed:** Claim approval timestamp, cutoff schedule, employer timezone/calendar.
- **Error message or user-facing explanation:** “This claim was approved after the monthly cutoff and is scheduled for next cycle.”
- **Edge cases:** Cutoff on non-business day; manual backdated approvals; daylight saving time shifts.

## BR-014 — Reimbursement Batch Timing
- **Plain-language rule:** Approved claims are paid in scheduled batches based on payment rails and funding readiness.
- **System behavior:**
  - Queue approved claims into ACH/check batches by cycle.
  - Hold payment if bank details are invalid or funding file fails validation.
  - Publish batch status transitions (queued, sent, settled, failed).
- **Configurable or hard-coded?** Configurable (batch frequency, lead times, rail-specific schedules).
- **Data needed:** Approved claim amount/date, payment method, bank/check details, batch schedule, funding status, return/reject codes.
- **Error message or user-facing explanation:** “Payment is delayed pending account verification or funding confirmation.”
- **Edge cases:** ACH return after settlement; negative adjustments netted against batch; holiday banking closures.

## BR-015 — Administrative Fees
- **Plain-language rule:** Administrative fees are assessed per employer contract and must be visible in reporting and billing.
- **System behavior:**
  - Calculate fees based on configured pricing model (PEPM, per-claim, hybrid, minimum invoice).
  - Separate participant reimbursements from employer invoicing ledger.
  - Generate monthly fee statements with auditable line items.
- **Configurable or hard-coded?** Configurable (contract-driven fee rules).
- **Data needed:** Employer contract terms, active participant counts, claim volume, invoice period, tax settings, credits/adjustments.
- **Error message or user-facing explanation:** “Administrative fees are calculated per your employer’s plan agreement and appear on employer billing statements.”
- **Edge cases:** Mid-month contract changes; retro credits; multi-entity billing hierarchies.

---

## Implementation Notes
- Store all date windows as timezone-aware timestamps and persist the timezone used for each employer/program.
- Version all policy configurations with effective dates for auditability and retro processing.
- Maintain immutable adjudication and communication logs tied to each claim state transition.
