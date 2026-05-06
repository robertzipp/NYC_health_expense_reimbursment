import React, { useMemo, useState } from 'react';
import { validateClaimForSubmit, validateExpense } from './claimRules.js';

const emptyExpense = {
  claimant: '',
  dateOfService: '',
  expenseCategory: '',
  amountCharged: '',
  requestedReimbursementAmount: '',
  serviceType: '',
  documentationRequired: true,
  documents: [],
};

export function ClaimBuilder({ initialClaim, apiClient }) {
  const [claim, setClaim] = useState(initialClaim ?? { status: 'Draft', expenses: [] });
  const [expense, setExpense] = useState(emptyExpense);
  const [errors, setErrors] = useState([]);
  const submitErrors = useMemo(() => validateClaimForSubmit(claim), [claim]);
  const canEdit = claim.status === 'Draft';

  async function addExpense(event) {
    event.preventDefault();
    const validation = validateExpense(expense);
    if (validation.length > 0) {
      setErrors(validation);
      return;
    }

    const saved = await apiClient.addExpense(claim.id, expense);
    setClaim({ ...claim, expenses: [...claim.expenses, saved] });
    setExpense(emptyExpense);
    setErrors([]);
  }

  async function submitClaim() {
    const validation = validateClaimForSubmit(claim);
    if (validation.length > 0) {
      setErrors(validation);
      return;
    }

    setClaim(await apiClient.submitClaim(claim.id));
    setErrors([]);
  }

  return (
    <section aria-labelledby="claim-builder-heading">
      <h2 id="claim-builder-heading">HCFSA claim</h2>
      <p>Status: {claim.status}</p>

      {!canEdit && <p role="status">Submitted claims are locked for employee edits.</p>}

      {canEdit && (
        <form onSubmit={addExpense}>
          <input aria-label="Claimant" value={expense.claimant} onChange={(event) => setExpense({ ...expense, claimant: event.target.value })} />
          <input aria-label="Date of service" type="date" value={expense.dateOfService} onChange={(event) => setExpense({ ...expense, dateOfService: event.target.value })} />
          <input aria-label="Expense category" value={expense.expenseCategory} onChange={(event) => setExpense({ ...expense, expenseCategory: event.target.value })} />
          <input aria-label="Amount charged" inputMode="decimal" value={expense.amountCharged} onChange={(event) => setExpense({ ...expense, amountCharged: event.target.value })} />
          <input aria-label="Requested reimbursement amount" inputMode="decimal" value={expense.requestedReimbursementAmount} onChange={(event) => setExpense({ ...expense, requestedReimbursementAmount: event.target.value })} />
          <input aria-label="Service type" value={expense.serviceType} onChange={(event) => setExpense({ ...expense, serviceType: event.target.value })} />
          <label>
            <input type="checkbox" checked={expense.documentationRequired} onChange={(event) => setExpense({ ...expense, documentationRequired: event.target.checked })} />
            Documentation required
          </label>
          <button type="submit">Add expense</button>
        </form>
      )}

      <ul aria-label="Claim expenses">
        {claim.expenses.map((item) => (
          <li key={item.id ?? `${item.claimant}-${item.dateOfService}`}>
            {item.claimant} — ${item.requestedReimbursementAmount} requested
          </li>
        ))}
      </ul>

      {errors.length > 0 && (
        <div role="alert">
          {errors.map((error) => <p key={`${error.field}-${error.issue}`}>{error.field}: {error.issue}</p>)}
        </div>
      )}

      <button type="button" disabled={!canEdit || submitErrors.length > 0} onClick={submitClaim}>Submit claim</button>
    </section>
  );
}
