-- Initial schema for the first HCFSA claim vertical slice.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE agencies (
    id TEXT PRIMARY KEY,
    agency_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE employees (
    id TEXT PRIMARY KEY,
    agency_id TEXT NOT NULL REFERENCES agencies(id),
    external_employee_number TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    employment_status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE claims (
    id TEXT PRIMARY KEY,
    agency_id TEXT NOT NULL REFERENCES agencies(id),
    employee_id TEXT NOT NULL REFERENCES employees(id),
    status TEXT NOT NULL CHECK (status IN ('Draft', 'Submitted')),
    submitted_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE claim_expenses (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    claimant TEXT NOT NULL,
    date_of_service TEXT NOT NULL,
    expense_category TEXT NOT NULL,
    amount_charged_cents INTEGER NOT NULL CHECK (amount_charged_cents >= 0),
    requested_reimbursement_cents INTEGER NOT NULL CHECK (requested_reimbursement_cents > 0),
    service_type TEXT NOT NULL,
    documentation_required INTEGER NOT NULL CHECK (documentation_required IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE claim_documents (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL REFERENCES claims(id),
    expense_id TEXT NOT NULL REFERENCES claim_expenses(id),
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
    checksum_sha256 TEXT,
    document_type TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE audit_events (
    id TEXT PRIMARY KEY,
    occurred_at TEXT NOT NULL DEFAULT (datetime('now')),
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    agency_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    correlation_id TEXT,
    details_json TEXT NOT NULL DEFAULT '{}',
    previous_hash TEXT,
    event_hash TEXT NOT NULL
);

CREATE INDEX idx_claims_employee ON claims(employee_id, status);
CREATE INDEX idx_claim_expenses_claim ON claim_expenses(claim_id);
CREATE INDEX idx_claim_documents_expense ON claim_documents(expense_id);
CREATE INDEX idx_audit_events_entity ON audit_events(entity_type, entity_id, occurred_at);
CREATE INDEX idx_audit_events_agency ON audit_events(agency_id, occurred_at);
