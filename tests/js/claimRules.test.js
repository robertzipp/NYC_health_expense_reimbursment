import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateClaimForSubmit, validateExpense } from '../../src/Hcfsa.Web/src/claimRules.js';

test('expense validation requires positive reimbursement not exceeding amount charged', () => {
  const details = validateExpense({
    claimant: 'Ava Lee',
    dateOfService: '2026-02-01',
    expenseCategory: 'medical',
    amountCharged: '45.00',
    requestedReimbursementAmount: '46.00',
    serviceType: 'copay',
  });

  assert.deepEqual(details, [
    { field: 'requested_reimbursement_amount', issue: 'must not exceed amount charged' },
  ]);
});

test('submit validation requires an expense and required supporting documents', () => {
  assert.deepEqual(validateClaimForSubmit({ expenses: [] }), [
    { field: 'expenses', issue: 'submitted claim must have at least one expense' },
  ]);

  const details = validateClaimForSubmit({
    expenses: [{
      id: 'expense-1',
      claimant: 'Ava Lee',
      dateOfService: '2026-02-01',
      expenseCategory: 'medical',
      amountCharged: '45.00',
      requestedReimbursementAmount: '45.00',
      serviceType: 'copay',
      documentationRequired: true,
      documents: [],
    }],
  });

  assert.equal(details.at(-1).issue, 'supporting document is required for this expense');
});

test('documentation-not-required expenses may submit without a document', () => {
  const details = validateClaimForSubmit({
    expenses: [{
      id: 'expense-1',
      claimant: 'Ava Lee',
      dateOfService: '2026-02-01',
      expenseCategory: 'medical',
      amountCharged: '45.00',
      requestedReimbursementAmount: '20.00',
      serviceType: 'auto_substantiated',
      documentationRequired: false,
      documents: [],
    }],
  });

  assert.deepEqual(details, []);
});

test('service creates required audit events and migration avoids document binaries', () => {
  const service = readFileSync('src/Hcfsa.Api/Claims/ClaimService.cs', 'utf8');
  for (const eventType of [
    'claim.created',
    'claim_expense.added',
    'claim_document.attached',
    'claim.submitted',
    'claim.validation_failed',
  ]) {
    assert.match(service, new RegExp(eventType.replace('.', '\\.')));
  }

  const migration = readFileSync('db/migrations/001_claim_submission_slice.sql', 'utf8').toLowerCase();
  assert.doesNotMatch(migration, /varbinary|image\s+not|null\s+image|documentbinary|filecontent|contentbytes/);
  assert.match(migration, /checksumsha256 char\(64\)/);
});
