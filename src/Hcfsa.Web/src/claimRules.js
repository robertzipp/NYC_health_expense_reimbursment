export function validateExpense(expense) {
  const details = [];
  required(expense.claimant, 'claimant', details);
  required(expense.dateOfService, 'date_of_service', details);
  required(expense.expenseCategory, 'expense_category', details);
  required(expense.serviceType, 'service_type', details);

  const amountCharged = parseMoney(expense.amountCharged);
  const requested = parseMoney(expense.requestedReimbursementAmount);

  if (amountCharged === null || amountCharged <= 0) {
    details.push({ field: 'amount_charged', issue: 'must be a positive money string' });
  }
  if (requested === null || requested <= 0) {
    details.push({ field: 'requested_reimbursement_amount', issue: 'must be greater than 0' });
  }
  if (amountCharged !== null && requested !== null && requested > amountCharged) {
    details.push({ field: 'requested_reimbursement_amount', issue: 'must not exceed amount charged' });
  }

  return details;
}

export function validateClaimForSubmit(claim) {
  const details = [];
  if (!claim.expenses || claim.expenses.length === 0) {
    details.push({ field: 'expenses', issue: 'submitted claim must have at least one expense' });
  }

  for (const expense of claim.expenses ?? []) {
    details.push(...validateExpense(expense));
    if (expense.documentationRequired !== false && (!expense.documents || expense.documents.length === 0)) {
      details.push({ field: `expenses.${expense.id}.documents`, issue: 'supporting document is required for this expense' });
    }
  }

  return details;
}

export function parseMoney(value) {
  if (typeof value !== 'string' || !/^\d+(\.\d{2})$/.test(value)) return null;
  return Number(value);
}

function required(value, field, details) {
  if (typeof value !== 'string' || value.trim() === '') {
    details.push({ field, issue: 'is required' });
  }
}
