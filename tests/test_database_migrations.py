from __future__ import annotations

import sqlite3
import unittest

from hcfsa.db import apply_migrations, connect, seed_minimal_reference_data


class DatabaseMigrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = connect()
        apply_migrations(self.conn)
        seed_minimal_reference_data(self.conn)
        self.conn.execute(
            "INSERT INTO claims (id, agency_id, employee_id, status) VALUES (?, ?, ?, ?)",
            ("claim-1", "agency-nyc", "employee-1", "Draft"),
        )
        self.conn.execute(
            """
            INSERT INTO claim_expenses (
                id, claim_id, claimant, date_of_service, expense_category,
                amount_charged_cents, requested_reimbursement_cents, service_type,
                documentation_required
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("expense-1", "claim-1", "Ava Lee", "2026-02-01", "medical", 4500, 4500, "copay", 1),
        )
        self.conn.commit()

    def test_document_metadata_triggers_reject_path_names_and_invalid_checksums(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                """
                INSERT INTO claim_documents (
                    id, claim_id, expense_id, file_name, mime_type, size_bytes,
                    checksum_sha256, document_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "document-1",
                    "claim-1",
                    "expense-1",
                    "../receipt.pdf",
                    "application/pdf",
                    123,
                    "not-a-sha",
                    "itemized_receipt",
                ),
            )


if __name__ == "__main__":
    unittest.main()
