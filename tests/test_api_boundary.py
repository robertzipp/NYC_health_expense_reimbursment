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


if __name__ == "__main__":
    unittest.main()
