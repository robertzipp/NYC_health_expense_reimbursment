from __future__ import annotations

import unittest

from hcfsa.api import ApiApp
from hcfsa.audit import ActorContext
from hcfsa.db import apply_migrations, connect, seed_minimal_reference_data
from hcfsa.service import ClaimService


class ClaimVerticalSliceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.conn = connect()
        apply_migrations(self.conn)
        seed_minimal_reference_data(self.conn)
        self.service = ClaimService(self.conn)
        self.app = ApiApp(self.service)
        self.actor = ActorContext("employee", "employee-1", "agency-nyc")
        self.headers = {
            "X-Actor-Type": "employee",
            "X-Actor-Id": "employee-1",
            "X-Agency-Id": "agency-nyc",
            "X-Correlation-Id": "test-correlation",
        }

    def test_employee_can_create_draft_add_expense_attach_doc_validate_and_submit(self) -> None:
        claim_response = self.app.handle("POST", "/api/v1/claims", self.headers, '{"employee_id":"employee-1"}')
        self.assertEqual(claim_response.status, 201)
        claim_id = claim_response.body["id"]
        self.assertEqual(claim_response.body["status"], "Draft")

        expense_response = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim_id}/expenses",
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
        self.assertEqual(expense_response.status, 201)
        expense_id = expense_response.body["id"]

        document_response = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim_id}/expenses/{expense_id}/documents",
            self.headers,
            """
            {
                "file_name": "receipt.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 12345,
                "checksum_sha256": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
                "document_type": "itemized_receipt"
            }
            """,
        )
        self.assertEqual(document_response.status, 201)

        validation_response = self.app.handle("POST", f"/api/v1/claims/{claim_id}/validate", self.headers, "{}")
        self.assertEqual(validation_response.status, 200)
        self.assertTrue(validation_response.body["valid"])

        submit_response = self.app.handle("POST", f"/api/v1/claims/{claim_id}/submit", self.headers, "{}")
        self.assertEqual(submit_response.status, 200)
        self.assertEqual(submit_response.body["status"], "Submitted")
        self.assertIsNotNone(submit_response.body["submitted_at"])

        fetched_response = self.app.handle("GET", f"/api/v1/claims/{claim_id}", self.headers)
        self.assertEqual(fetched_response.status, 200)
        self.assertEqual(len(fetched_response.body["expenses"]), 1)
        self.assertEqual(len(fetched_response.body["expenses"][0]["documents"]), 1)

        audit_response = self.app.handle(
            "GET", f"/api/v1/audit-events?entity_type=claim&entity_id={claim_id}", self.headers
        )
        self.assertEqual(audit_response.status, 200)
        event_types = [event["event_type"] for event in audit_response.body["data"]]
        self.assertEqual(
            event_types,
            ["claim.created", "claim_expense.added", "claim_document.attached", "claim.submitted"],
        )

    def test_submit_without_expense_fails_and_audits_validation_failure(self) -> None:
        claim = self.service.create_claim(self.actor, {"employee_id": "employee-1"})

        response = self.app.handle("POST", f"/api/v1/claims/{claim['id']}/submit", self.headers, "{}")

        self.assertEqual(response.status, 422)
        self.assertEqual(response.body["error"]["code"], "BUSINESS_RULE_VIOLATION")
        events = self.service.audit_events_for_claim(self.actor, claim["id"])
        self.assertEqual(events[-1]["event_type"], "claim.validation_failed")
        self.assertEqual(events[-1]["outcome"], "failure")

    def test_submit_with_document_required_expense_without_document_fails(self) -> None:
        claim = self.service.create_claim(self.actor, {"employee_id": "employee-1"})
        self.service.add_expense(
            self.actor,
            claim["id"],
            {
                "claimant": "Ava Lee",
                "date_of_service": "2026-02-01",
                "expense_category": "medical",
                "amount_charged": "45.00",
                "requested_reimbursement_amount": "45.00",
                "service_type": "copay",
            },
        )

        response = self.app.handle("POST", f"/api/v1/claims/{claim['id']}/submit", self.headers, "{}")

        self.assertEqual(response.status, 422)
        self.assertIn("supporting document", response.body["error"]["details"][0]["issue"])

    def test_documentation_not_required_expense_can_submit_without_document(self) -> None:
        claim = self.service.create_claim(self.actor, {"employee_id": "employee-1"})
        self.service.add_expense(
            self.actor,
            claim["id"],
            {
                "claimant": "Ava Lee",
                "date_of_service": "2026-02-01",
                "expense_category": "medical",
                "amount_charged": "45.00",
                "requested_reimbursement_amount": "20.00",
                "service_type": "auto_substantiated",
                "documentation_required": False,
            },
        )

        response = self.app.handle("POST", f"/api/v1/claims/{claim['id']}/submit", self.headers, "{}")

        self.assertEqual(response.status, 200)
        self.assertEqual(response.body["status"], "Submitted")

    def test_requested_reimbursement_must_be_positive_and_not_exceed_amount_charged(self) -> None:
        claim = self.service.create_claim(self.actor, {"employee_id": "employee-1"})

        response = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim['id']}/expenses",
            self.headers,
            """
            {
                "claimant": "Ava Lee",
                "date_of_service": "2026-02-01",
                "expense_category": "medical",
                "amount_charged": "45.00",
                "requested_reimbursement_amount": "46.00",
                "service_type": "copay"
            }
            """,
        )

        self.assertEqual(response.status, 400)
        self.assertEqual(response.body["error"]["details"][0]["field"], "requested_reimbursement_amount")

    def test_claim_cannot_be_submitted_twice_or_edited_after_submission(self) -> None:
        claim = self.service.create_claim(self.actor, {"employee_id": "employee-1"})
        expense = self.service.add_expense(
            self.actor,
            claim["id"],
            {
                "claimant": "Ava Lee",
                "date_of_service": "2026-02-01",
                "expense_category": "medical",
                "amount_charged": "45.00",
                "requested_reimbursement_amount": "45.00",
                "service_type": "copay",
            },
        )
        self.service.attach_document(
            self.actor,
            claim["id"],
            expense["id"],
            {
                "file_name": "receipt.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 123,
                "document_type": "itemized_receipt",
            },
        )
        self.service.submit_claim(self.actor, claim["id"])

        second_submit = self.app.handle("POST", f"/api/v1/claims/{claim['id']}/submit", self.headers, "{}")
        self.assertEqual(second_submit.status, 409)

        edit_response = self.app.handle(
            "POST",
            f"/api/v1/claims/{claim['id']}/expenses",
            self.headers,
            """
            {
                "claimant": "Ava Lee",
                "date_of_service": "2026-02-02",
                "expense_category": "medical",
                "amount_charged": "10.00",
                "requested_reimbursement_amount": "10.00",
                "service_type": "copay"
            }
            """,
        )
        self.assertEqual(edit_response.status, 409)

    def test_employee_cannot_access_another_employee_claim(self) -> None:
        self.conn.execute(
            """
            INSERT INTO employees (id, agency_id, external_employee_number, first_name, last_name, employment_status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("employee-2", "agency-nyc", "EMP-2", "Ben", "Ng", "active"),
        )
        self.conn.commit()
        other_actor = ActorContext("employee", "employee-2", "agency-nyc")
        claim = self.service.create_claim(other_actor, {"employee_id": "employee-2"})

        response = self.app.handle("GET", f"/api/v1/claims/{claim['id']}", self.headers)

        self.assertEqual(response.status, 403)


if __name__ == "__main__":
    unittest.main()
