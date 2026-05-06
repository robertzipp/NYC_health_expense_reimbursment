# HCFSA Employee-Facing Text Wireframe Specifications

## 1) Dashboard

### Purpose
Provide employees with a single glance view of account status, active claims, required actions, and next steps.

### Primary user question
“What do I need to do right now, and what is the current status of my HCFSA money and claims?”

### Fields
- Plan year (e.g., 2026)
- Annual election amount
- Year-to-date contributions
- Available balance
- Pending claim amount
- Reimbursed amount YTD
- Upcoming deadlines (run-out date, documentation due date)
- Claim list summary (claim ID, date submitted, amount, status)
- Alerts/notifications list

### Calls to action
- Start new claim
- View claim details
- Respond to missing information
- View receipt locker
- Start enrollment / Edit election (during open enrollment)
- Download account statement

### Validation messages
- “Unable to calculate current balance. Please refresh.”
- “Plan year could not be loaded. Try again.”

### Empty states
- No claims yet: “You have not submitted any claims this plan year.”
- No alerts: “You’re all caught up. No actions required.”
- No receipts in locker preview: “No receipts saved yet.”

### Error states
- Dashboard service unavailable: “We can’t load your dashboard right now.”
- Partial load error: show available widgets, with inline widget-level retry links.
- Session timeout redirect to sign-in with return path.

### Accessibility notes
- Use semantic headings for each dashboard card region.
- Announce alert banner updates via ARIA live region.
- Ensure color is not sole status indicator; include icon + text labels.
- Keyboard focus order must follow visual hierarchy.

### Content guidance
- Lead with action-oriented copy (“2 claims need your response”).
- Use plain language for benefit terms; provide tooltip glossary for “run-out period.”
- Show dates in long format with timezone context where relevant.

---

## 2) Start Claim

### Purpose
Capture high-level claim setup details and route users into expense entry.

### Primary user question
“How do I begin a reimbursement claim correctly?”

### Fields
- Plan year selector
- Service date range (from/to)
- Recipient (self/spouse/dependent)
- Provider/merchant name (optional at this step)
- Quick category selector (medical, dental, vision, pharmacy, other)

### Calls to action
- Continue to Add expense
- Save draft
- Cancel

### Validation messages
- “Select a plan year to continue.”
- “Enter a valid service date.”
- “Service date must be within the eligible claim window.”
- “Choose who received the service.”

### Empty states
- First-time user helper panel with “How claims work.”

### Error states
- Eligibility lookup failed: “We can’t verify eligibility right now. You may save as draft and return later.”
- Draft save failed: “Draft was not saved. Try again.”

### Accessibility notes
- Date fields support keyboard entry and accessible calendar picker.
- Group radio controls (recipient/category) with fieldset + legend.
- Error summary at top links to invalid fields.

### Content guidance
- Explain that one claim can contain multiple expenses if allowed by policy.
- Provide examples for date and category choices.

---

## 3) Add Expense

### Purpose
Collect line-item expense details required for adjudication.

### Primary user question
“What information is needed for each expense I want reimbursed?”

### Fields
- Expense type/category
- Date of service
- Amount requested
- Provider/merchant
- Description of service/item
- Recipient associated with expense
- Quantity (optional)
- Coordination of benefits indicator (if covered elsewhere)

### Calls to action
- Add expense line
- Edit line
- Remove line
- Save and continue
- Save draft

### Validation messages
- “Enter an amount greater than $0.00.”
- “Amount cannot exceed two decimal places.”
- “Date of service cannot be in the future.”
- “Provider name is required for this expense type.”

### Empty states
- “No expense lines added yet.”
- Inline prompt: “Add at least one expense to continue.”

### Error states
- Duplicate detection warning: “This expense may already exist in a submitted claim.”
- Save interruption: “We couldn’t save this expense line.”

### Accessibility notes
- Dynamic expense rows announce add/remove actions via polite live region.
- Table/list layout must be fully operable by keyboard.
- Currency input includes programmatic label and format hint.

### Content guidance
- Clarify differences between “date purchased” and “date of service.”
- Use non-technical terms for coordination-of-benefits question.

---

## 4) Upload Documentation

### Purpose
Attach required supporting documents for each expense.

### Primary user question
“What files do I need to upload, and are they acceptable?”

### Fields
- File uploader (drag/drop + browse)
- Document type (receipt, EOB, itemized invoice, prescription, other)
- Expense line association selector
- Optional note

### Calls to action
- Upload file
- Replace file
- Remove file
- Continue to review
- Save draft

### Validation messages
- “File type not supported. Upload PDF, JPG, PNG, or HEIC.”
- “File exceeds maximum size (10 MB).”
- “Attach at least one document for each required expense line.”
- “Document type is required.”

### Empty states
- “No documents uploaded yet.”
- Contextual checklist of required documentation by expense type.

### Error states
- Upload failed (network): “Upload interrupted. Retry upload.”
- Malware scan failed: “This file cannot be accepted. Upload a different file.”
- OCR/preview failed but file stored: “Preview unavailable; file uploaded successfully.”

### Accessibility notes
- Uploader must support keyboard-only file selection.
- Progress indicators are text-based in addition to visual bars.
- Associate upload errors with specific file rows.

### Content guidance
- Explain what makes a receipt “itemized.”
- Encourage removing sensitive unrelated data where permissible.

---

## 5) Claim Completeness Review

### Purpose
Verify all required claim information and documentation before submission.

### Primary user question
“Is my claim complete and likely ready to submit?”

### Fields
- Read-only summary: claimant, plan year, total amount
- Expense line checklist with completeness status
- Documentation checklist per line item
- Missing items panel
- Attestation checkbox

### Calls to action
- Edit claim details
- Add missing documentation
- Submit claim
- Save draft

### Validation messages
- “You must acknowledge the attestation to submit.”
- “1 expense line is missing required documentation.”

### Empty states
- If no claim data: “No draft claim found.” with CTA to start claim.

### Error states
- Completeness rules engine unavailable: “Unable to run final checks. Try again.”
- Submit blocked due to stale data: “Your claim was updated in another session. Refresh required.”

### Accessibility notes
- Checklist uses accessible status text (Complete/Incomplete).
- Error summary focuses first invalid section on submit attempt.

### Content guidance
- Frame issues as fixable steps (“Add EOB for expense #2”).
- Keep attestation language legally precise but plain.

---

## 6) Submit Claim Confirmation

### Purpose
Confirm successful submission and provide tracking details.

### Primary user question
“Was my claim submitted, and what happens next?”

### Fields
- Confirmation number / claim ID
- Submission timestamp
- Total submitted amount
- Expected processing timeline
- Communication preferences summary

### Calls to action
- View claim status detail
- Download/print confirmation
- Start another claim
- Return to dashboard

### Validation messages
- Not applicable (read-only confirmation)

### Empty states
- If no recent submission in context: “No submission found.” with navigation options.

### Error states
- Confirmation retrieval failed after submit: “Your claim may have been submitted. Check claim history.”

### Accessibility notes
- Place success heading at top and move focus there after submission.
- Provide confirmation number in selectable text for assistive copying.

### Content guidance
- Set realistic SLAs and clarify that additional documentation may still be requested.

---

## 7) Receipt Locker

### Purpose
Allow users to store, organize, and reuse documentation independent of immediate claim submission.

### Primary user question
“Where can I keep receipts so I can attach them to claims later?”

### Fields
- Receipt list (filename, upload date, size, tag/category)
- Search field
- Filter chips (year, category, attached/unattached)
- Bulk select checkbox
- Receipt metadata editor (optional note, service date)

### Calls to action
- Upload receipt
- Tag receipt
- Attach to claim
- Download
- Delete

### Validation messages
- “Select at least one receipt to perform bulk action.”
- “Tag exceeds 50 characters.”

### Empty states
- “Your receipt locker is empty.” with upload CTA.
- No results for search/filter state.

### Error states
- Retrieval failure: “Unable to load receipts.”
- Delete failure with recovery message and retry.

### Accessibility notes
- Data table/list provides row headers and sortable control labels.
- Multi-select interactions expose state to screen readers.

### Content guidance
- Clarify retention policy and privacy handling.
- Suggest consistent naming/tags for easier retrieval.

---

## 8) Enrollment Start

### Purpose
Initiate annual enrollment flow for HCFSA elections.

### Primary user question
“How do I start or update my HCFSA enrollment for the next plan year?”

### Fields
- Plan year
- Employment eligibility status (read-only)
- Open enrollment window dates
- Prior year election amount (read-only)

### Calls to action
- Start enrollment
- Learn about HCFSA rules
- Decline enrollment

### Validation messages
- “Enrollment is not currently open for the selected plan year.”

### Empty states
- Not eligible state with explanation and support contact.

### Error states
- Eligibility service error: “We can’t verify enrollment eligibility at this time.”

### Accessibility notes
- Eligibility badges include text equivalents.
- Date information announced in complete sentence format.

### Content guidance
- Emphasize use-it-or-lose-it and carryover/grace rules as configured.

---

## 9) Contribution Election

### Purpose
Capture annual pre-tax contribution amount with payroll impact visibility.

### Primary user question
“How much should I contribute, and what will it mean per paycheck?”

### Fields
- Annual election amount input
- Employer min/max limits (read-only)
- Recommended range helper (optional)
- Pay frequency
- Estimated per-paycheck deduction
- Acknowledgment checkbox for tax implications

### Calls to action
- Continue
- Recalculate estimate
- Save and exit

### Validation messages
- “Enter a whole dollar amount within allowed limits.”
- “Election exceeds IRS annual limit.”
- “You must acknowledge tax implications to continue.”

### Empty states
- If pay schedule unavailable: show generic estimate disclaimer.

### Error states
- Payroll estimate service unavailable: “Deduction estimate is temporarily unavailable.”

### Accessibility notes
- Instant recalculation updates announced via live region.
- Input hint text tied programmatically to election field.

### Content guidance
- Avoid financial advice tone; provide neutral planning tips.
- Distinguish hard limits from recommendations.

---

## 10) Eligible Recipients

### Purpose
Collect and validate who can incur eligible expenses under the employee’s account.

### Primary user question
“Who can I include for eligible HCFSA expenses?”

### Fields
- Recipient list (self prefilled, spouse/dependents)
- Relationship
- First/last name
- Date of birth
- Tax dependent status
- Optional SSN last-4 (if required by policy)

### Calls to action
- Add recipient
- Edit recipient
- Remove recipient
- Continue

### Validation messages
- “Recipient date of birth is required.”
- “Dependent does not meet eligibility rules for this plan year.”
- “Duplicate recipient detected.”

### Empty states
- No dependents added state with explanation that self-only is allowed.

### Error states
- Dependent verification timeout: allow save with pending verification status.

### Accessibility notes
- Repeating form groups use clear headings (“Dependent 1,” etc.)
- Date fields support screen-reader friendly input masks.

### Content guidance
- Explain in plain terms what “tax dependent” means in this context.
- Clearly state required vs optional PII fields.

---

## 11) Enrollment Review

### Purpose
Provide final pre-submission review of enrollment selections.

### Primary user question
“Is everything correct before I submit my enrollment?”

### Fields
- Read-only summary: plan year, election amount, payroll estimate
- Recipient summary
- Legal acknowledgments/attestations
- Effective date

### Calls to action
- Edit contribution
- Edit recipients
- Submit enrollment
- Save draft

### Validation messages
- “You must accept all required acknowledgments before submitting.”

### Empty states
- “No enrollment data found.” with return path to start enrollment.

### Error states
- Submission error with unknown status: “Submission in progress. Do not resubmit; check status in a few minutes.”

### Accessibility notes
- Review sections use definition-list or table semantics appropriately.
- Submit action has clear accessible name (“Submit HCFSA enrollment”).

### Content guidance
- Reinforce deadline/time cutoff and when elections take effect.

---

## 12) Claim Status Detail

### Purpose
Show granular lifecycle updates for a submitted claim and available next steps.

### Primary user question
“Where is my claim in the process, and what do I need to do next?”

### Fields
- Claim ID and submission date
- Current status (received, in review, approved, partial, denied, paid)
- Timeline/history log with timestamps
- Line-item adjudication outcomes
- Payment details (method, date, amount)
- Outstanding tasks (if any)

### Calls to action
- Respond to missing info
- Download determination letter
- View denial detail
- Start appeal
- Contact support

### Validation messages
- “This claim is not eligible for appeal at this stage.”

### Empty states
- If claim not found: “We couldn’t find that claim.” with history link.

### Error states
- Status feed unavailable: “Real-time updates unavailable; showing last known status.”

### Accessibility notes
- Timeline is readable linearly for screen readers.
- Status badges include text and not color-only indicators.

### Content guidance
- Use plain status definitions (“In review means…”).
- Highlight action deadlines prominently.

---

## 13) Missing Information Response

### Purpose
Enable users to satisfy follow-up requests for additional claim details.

### Primary user question
“What exactly is missing, and how do I provide it correctly?”

### Fields
- Request summary (what is needed and due date)
- Affected expense lines
- Response text area (optional)
- File upload for supplemental documents
- Contact preference for follow-up

### Calls to action
- Upload requested documents
- Submit response
- Save draft
- Ask for clarification

### Validation messages
- “At least one requested document is required.”
- “Response deadline has passed. Contact support.”

### Empty states
- No active requests: “There are no open requests for this claim.”

### Error states
- Submit failure with idempotency warning: “We couldn’t confirm submission. Do not resubmit immediately; refresh status first.”

### Accessibility notes
- Display due date with urgency text, not color alone.
- Attachments list exposes filename, status, and remove control labels.

### Content guidance
- Provide exact examples of acceptable documents.
- Avoid accusatory wording; emphasize assistance.

---

## 14) Denial Detail

### Purpose
Explain denial outcomes and inform users of options and deadlines.

### Primary user question
“Why was my claim denied, and what can I do now?”

### Fields
- Denial reason code(s)
- Human-readable denial explanation
- Policy/rule references
- Denied line items and amounts
- Appeal eligibility + deadline
- Determination document link

### Calls to action
- Start appeal
- Upload corrected documentation (if reopening allowed)
- Contact support

### Validation messages
- “Appeal window has closed for this determination.”

### Empty states
- If no denial exists: redirect or message “This claim has no denial record.”

### Error states
- Determination document unavailable: show fallback summary and support path.

### Accessibility notes
- Denial reasons presented as structured list with clear headings.
- Links to policy references have descriptive link text.

### Content guidance
- Separate factual determination from guidance on next steps.
- Keep legal/policy text scannable with summaries.

---

## 15) Appeal Submission

### Purpose
Collect appeal rationale and supporting evidence for denied claims.

### Primary user question
“How do I submit a complete and timely appeal?”

### Fields
- Appeal subject (prefilled claim/line reference)
- Appeal reason selection
- Narrative statement text area
- Supporting document uploads
- Attestation + signature acknowledgment

### Calls to action
- Submit appeal
- Save draft
- Cancel

### Validation messages
- “Select at least one appeal reason.”
- “Provide an appeal statement (minimum 50 characters).”
- “At least one supporting document is required.”
- “You must acknowledge certification before submission.”

### Empty states
- If claim not appealable: “This claim cannot be appealed.” with support CTA.

### Error states
- Deadline passed while in form: block submit and preserve draft.
- Upload/submit conflict: “Some files are still processing. Wait before submitting.”

### Accessibility notes
- Large text area includes character guidance and screen-reader count updates.
- Error summary appears on submit and links to each invalid field.

### Content guidance
- Encourage objective, specific statements tied to documentation.
- Clearly state decision timeline and communication channel post-appeal.
