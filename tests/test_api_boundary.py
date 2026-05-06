from __future__ import annotations

import unittest

from hcfsa.api import ApiApp
from hcfsa.db import apply_migrations, connect, seed_minimal_reference_data
from hcfsa.service import ClaimService


class ApiBoundaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = connect()
        apply_migrations(self.conn)
        seed_minimal_reference_data(self.conn)
        self.app = ApiApp(ClaimService(self.conn))
        self.headers = {
            "X-Actor-Type": "employee",
            "X-Actor-Id": "employee-1",
            "X-Agency-Id": "agency-nyc",
        }

    def test_missing_actor_context_returns_error_envelope(self) -> None:
        response = self.app.handle("POST", "/api/v1/claims", {}, '{"employee_id":"employee-1"}')

        self.assertEqual(response.status, 400)
        self.assertEqual(response.body["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response.body["error"]["details"][0]["field"], "X-Actor-Type")

    def test_invalid_json_returns_error_envelope(self) -> None:
        response = self.app.handle("POST", "/api/v1/claims", self.headers, "{")

        self.assertEqual(response.status, 400)
        self.assertEqual(response.body["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(response.body["error"]["details"][0]["field"], "body")

    def test_invalid_money_float_is_rejected_at_api_boundary(self) -> None:
        claim = self.app.handle("POST", "/api/v1/claims", self.headers, '{"employee_id":"employee-1"}')

        response = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim.body['id']}/expenses",
            self.headers,
            """
            {
                "claimant": "Ava Lee",
                "date_of_service": "2026-02-01",
                "expense_category": "medical",
                "amount_charged": 45.00,
                "requested_reimbursement_amount": "45.00",
                "service_type": "copay"
            }
            """,
        )

        self.assertEqual(response.status, 400)
        self.assertEqual(response.body["error"]["details"][0]["field"], "amount_charged")

    def test_invalid_calendar_date_is_rejected(self) -> None:
        claim = self.app.handle("POST", "/api/v1/claims", self.headers, '{"employee_id":"employee-1"}')

        response = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim.body['id']}/expenses",
            self.headers,
            """
            {
                "claimant": "Ava Lee",
                "date_of_service": "2026-02-31",
                "expense_category": "medical",
                "amount_charged": "45.00",
                "requested_reimbursement_amount": "45.00",
                "service_type": "copay"
            }
            """,
        )

        self.assertEqual(response.status, 400)
        self.assertEqual(response.body["error"]["details"][0]["field"], "date_of_service")
        self.assertEqual(response.body["error"]["details"][0]["issue"], "must be a valid calendar date")

    def test_document_metadata_boundary_validation(self) -> None:
        claim = self.app.handle("POST", "/api/v1/claims", self.headers, '{"employee_id":"employee-1"}')
        expense = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim.body['id']}/expenses",
            self.headers,
            """
            {
                "claimant": "Ava Lee",
                "date_of_service": "2026-02-01",
                "expense_category": "medical",
                "amount_charged": "45.00",
                "requested_reimbursement_amount": "45.00",
                "service_type": "copay"
            }
            """,
        )

        response = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim.body['id']}/expenses/{expense.body['id']}/documents",
            self.headers,
            """
            {
                "file_name": "../receipt.exe",
                "mime_type": "application/octet-stream",
                "size_bytes": 0,
                "checksum_sha256": "not-a-sha",
                "document_type": "itemized_receipt"
            }
            """,
        )

        self.assertEqual(response.status, 400)
        details = response.body["error"]["details"]
        self.assertEqual(details[0]["field"], "file_name")
        self.assertIn({"field": "mime_type", "issue": "unsupported file type"}, details)
        self.assertIn({"field": "size_bytes", "issue": "must be greater than 0"}, details)
        self.assertIn(
            {"field": "checksum_sha256", "issue": "must be a 64-character hexadecimal SHA-256"},
            details,
        )

    def test_document_metadata_checksum_is_normalized_without_storing_binaries(self) -> None:
        claim = self.app.handle("POST", "/api/v1/claims", self.headers, '{"employee_id":"employee-1"}')
        expense = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim.body['id']}/expenses",
            self.headers,
            """
            {
                "claimant": "Ava Lee",
                "date_of_service": "2026-02-01",
                "expense_category": "medical",
                "amount_charged": "45.00",
                "requested_reimbursement_amount": "45.00",
                "service_type": "copay"
            }
            """,
        )
        checksum = "ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789"

        response = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim.body['id']}/expenses/{expense.body['id']}/documents",
            self.headers,
            f"""
            {{
                "file_name": "receipt.pdf",
                "mime_type": "APPLICATION/PDF",
                "size_bytes": 123,
                "checksum_sha256": "{checksum}",
                "document_type": "itemized_receipt",
                "content": "must-not-be-persisted"
            }}
            """,
        )

        self.assertEqual(response.status, 201)
        self.assertEqual(response.body["checksum_sha256"], checksum.lower())
        self.assertNotIn("content", response.body)


if __name__ == "__main__":
    unittest.main()
