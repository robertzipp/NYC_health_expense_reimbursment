from __future__ import annotations

import re
import sqlite3


def _regexp(pattern: str, value: object) -> int:
    return 1 if isinstance(value, str) and re.match(pattern, value) else 0


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.create_function("regexp", 2, _regexp)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            agency_id TEXT NOT NULL,
            external_employee_number TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            employment_status TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS claims (
            id TEXT PRIMARY KEY,
            agency_id TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('Draft', 'Submitted')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            submitted_at TEXT
        );

        CREATE TABLE IF NOT EXISTS claim_expenses (
            id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
            claimant TEXT NOT NULL,
            date_of_service TEXT NOT NULL,
            expense_category TEXT NOT NULL,
            amount_charged_cents INTEGER NOT NULL CHECK (amount_charged_cents > 0),
            requested_reimbursement_cents INTEGER NOT NULL CHECK (requested_reimbursement_cents > 0 AND requested_reimbursement_cents <= amount_charged_cents),
            service_type TEXT NOT NULL,
            documentation_required INTEGER NOT NULL DEFAULT 1 CHECK (documentation_required IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS claim_documents (
            id TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
            expense_id TEXT NOT NULL REFERENCES claim_expenses(id) ON DELETE CASCADE,
            saved_receipt_id TEXT REFERENCES saved_receipts(id),
            file_name TEXT NOT NULL CHECK (instr(file_name, '/') = 0 AND instr(file_name, '\\') = 0),
            mime_type TEXT NOT NULL CHECK (mime_type IN ('application/pdf', 'image/jpeg', 'image/png')),
            size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
            checksum_sha256 TEXT NOT NULL CHECK (length(checksum_sha256) = 64 AND checksum_sha256 regexp '^[a-f0-9]{64}$'),
            document_type TEXT NOT NULL,
            attached_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS saved_receipts (
            id TEXT PRIMARY KEY,
            agency_id TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            file_name TEXT NOT NULL CHECK (instr(file_name, '/') = 0 AND instr(file_name, '\\') = 0),
            mime_type TEXT NOT NULL CHECK (mime_type IN ('application/pdf', 'image/jpeg', 'image/png')),
            size_bytes INTEGER NOT NULL CHECK (size_bytes > 0),
            checksum_sha256 TEXT NOT NULL CHECK (length(checksum_sha256) = 64 AND checksum_sha256 regexp '^[a-f0-9]{64}$'),
            document_type TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL CHECK (status IN ('Available', 'Attached', 'Archived')),
            claim_id TEXT REFERENCES claims(id),
            expense_id TEXT REFERENCES claim_expenses(id),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            attached_at TEXT,
            archived_at TEXT,
            CHECK ((status = 'Attached') = (claim_id IS NOT NULL AND expense_id IS NOT NULL AND attached_at IS NOT NULL)),
            CHECK (status != 'Archived' OR archived_at IS NOT NULL)
        );

        CREATE TABLE IF NOT EXISTS audit_events (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL CHECK (event_type IN (
                'claim.created', 'claim_expense.added', 'claim_document.attached', 'claim.submitted', 'claim.validation_failed',
                'receipt.created', 'receipt.updated', 'receipt.archived', 'receipt.attached'
            )),
            outcome TEXT NOT NULL CHECK (outcome IN ('success', 'failure')),
            entity_type TEXT NOT NULL CHECK (entity_type IN ('claim', 'receipt')),
            entity_id TEXT NOT NULL,
            actor_type TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            agency_id TEXT NOT NULL,
            correlation_id TEXT,
            occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data TEXT NOT NULL DEFAULT '{}'
        );
        """
    )
    conn.commit()


def seed_minimal_reference_data(conn: sqlite3.Connection) -> None:
    conn.commit()
