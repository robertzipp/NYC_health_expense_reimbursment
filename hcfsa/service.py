from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from .audit import ActorContext, AuditService
from .errors import BusinessRuleViolation, ConflictError, ForbiddenError, NotFoundError, ValidationError

DRAFT = "Draft"
SUBMITTED = "Submitted"
DOCUMENTATION_NOT_REQUIRED_TYPES = {"documentation_not_required", "auto_substantiated"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/heic"}

MONEY_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ClaimService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.audit = AuditService(conn)

    def create_claim(self, actor: ActorContext, payload: dict[str, object], correlation_id: str | None = None) -> dict[str, object]:
        self._require_employee_actor(actor)
        employee_id = self._required_str(payload, "employee_id")
        if employee_id != actor.actor_id:
            raise ForbiddenError("Employees can only create their own claims")
        employee = self._employee(employee_id)
        if employee["agency_id"] != actor.agency_id:
            raise ForbiddenError("Employee is outside actor agency")
        claim_id = str(uuid4())
        with self.conn:
            self.conn.execute(
                "INSERT INTO claims (id, agency_id, employee_id, status) VALUES (?, ?, ?, ?)",
                (claim_id, actor.agency_id, employee_id, DRAFT),
            )
            self.audit.record(
                actor=actor,
                event_type="claim.created",
                entity_type="claim",
                entity_id=claim_id,
                correlation_id=correlation_id,
            )
        return self.get_claim(actor, claim_id)

    def add_expense(
        self, actor: ActorContext, claim_id: str, payload: dict[str, object], correlation_id: str | None = None
    ) -> dict[str, object]:
        claim = self._claim_for_employee_edit(actor, claim_id)
        claimant = self._required_str(payload, "claimant")
        date_of_service = self._required_date(payload, "date_of_service")
        expense_category = self._required_str(payload, "expense_category")
        service_type = self._required_str(payload, "service_type")
        amount_charged_cents = self._required_money_cents(payload, "amount_charged")
        requested_cents = self._required_money_cents(payload, "requested_reimbursement_amount")
        documentation_required = self._documentation_required(payload, expense_category, service_type)
        details: list[dict[str, str]] = []
        if requested_cents <= 0:
            details.append({"field": "requested_reimbursement_amount", "issue": "must be greater than 0"})
        if requested_cents > amount_charged_cents:
            details.append(
                {"field": "requested_reimbursement_amount", "issue": "must not exceed amount_charged"}
            )
        if details:
            raise ValidationError(details=details)
        expense_id = str(uuid4())
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO claim_expenses (
                    id, claim_id, claimant, date_of_service, expense_category,
                    amount_charged_cents, requested_reimbursement_cents, service_type,
                    documentation_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    expense_id,
                    claim_id,
                    claimant,
                    date_of_service,
                    expense_category,
                    amount_charged_cents,
                    requested_cents,
                    service_type,
                    1 if documentation_required else 0,
                ),
            )
            self.audit.record(
                actor=actor,
                event_type="claim_expense.added",
                entity_type="claim",
                entity_id=claim_id,
                correlation_id=correlation_id,
                details={"expense_id": expense_id},
            )
        return self._expense_response(self._expense(expense_id))

    def attach_document(
        self,
        actor: ActorContext,
        claim_id: str,
        expense_id: str,
        payload: dict[str, object],
        correlation_id: str | None = None,
    ) -> dict[str, object]:
        self._claim_for_employee_edit(actor, claim_id)
        expense = self._expense(expense_id)
        if expense["claim_id"] != claim_id:
            raise NotFoundError("Expense not found for claim")
        file_name = self._required_str(payload, "file_name")
        mime_type = self._required_str(payload, "mime_type")
        document_type = self._required_str(payload, "document_type")
        size_bytes = self._required_int(payload, "size_bytes")
        checksum_sha256 = payload.get("checksum_sha256")
        details: list[dict[str, str]] = []
        if mime_type not in ALLOWED_MIME_TYPES:
            details.append({"field": "mime_type", "issue": "unsupported file type"})
        if size_bytes <= 0:
            details.append({"field": "size_bytes", "issue": "must be greater than 0"})
        if checksum_sha256 is not None and not isinstance(checksum_sha256, str):
            details.append({"field": "checksum_sha256", "issue": "must be a string"})
        if details:
            raise ValidationError(details=details)
        document_id = str(uuid4())
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO claim_documents (
                    id, claim_id, expense_id, file_name, mime_type, size_bytes,
                    checksum_sha256, document_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (document_id, claim_id, expense_id, file_name, mime_type, size_bytes, checksum_sha256, document_type),
            )
            self.audit.record(
                actor=actor,
                event_type="claim_document.attached",
                entity_type="claim",
                entity_id=claim_id,
                correlation_id=correlation_id,
                details={"expense_id": expense_id, "document_id": document_id},
            )
        return self._document_response(self._document(document_id))

    def validate_claim(self, actor: ActorContext, claim_id: str, correlation_id: str | None = None) -> dict[str, object]:
        self._claim_for_actor(actor, claim_id)
        result = self._validate_claim(claim_id)
        if not result["valid"]:
            with self.conn:
                self.audit.record(
                    actor=actor,
                    event_type="claim.validation_failed",
                    entity_type="claim",
                    entity_id=claim_id,
                    outcome="failure",
                    correlation_id=correlation_id,
                    details={"issues": result["errors"]},
                )
        return result

    def submit_claim(
        self, actor: ActorContext, claim_id: str, correlation_id: str | None = None
    ) -> dict[str, object]:
        claim = self._claim_for_employee_edit(actor, claim_id)
        if claim["status"] != DRAFT:
            raise ConflictError("Claim cannot be submitted twice")
        result = self._validate_claim(claim_id)
        if not result["valid"]:
            with self.conn:
                self.audit.record(
                    actor=actor,
                    event_type="claim.validation_failed",
                    entity_type="claim",
                    entity_id=claim_id,
                    outcome="failure",
                    correlation_id=correlation_id,
                    details={"issues": result["errors"]},
                )
            raise BusinessRuleViolation("Claim is not ready for submission", result["errors"])
        submitted_at = datetime.now(timezone.utc).isoformat()
        with self.conn:
            self.conn.execute(
                "UPDATE claims SET status = ?, submitted_at = ?, updated_at = datetime('now') WHERE id = ?",
                (SUBMITTED, submitted_at, claim_id),
            )
            self.audit.record(
                actor=actor,
                event_type="claim.submitted",
                entity_type="claim",
                entity_id=claim_id,
                correlation_id=correlation_id,
            )
        return self.get_claim(actor, claim_id)

    def get_claim(self, actor: ActorContext, claim_id: str) -> dict[str, object]:
        claim = self._claim_for_actor(actor, claim_id)
        expenses = [self._expense_response(row) for row in self._expenses_for_claim(claim_id)]
        return {
            "id": claim["id"],
            "employee_id": claim["employee_id"],
            "agency_id": claim["agency_id"],
            "status": claim["status"],
            "submitted_at": claim["submitted_at"],
            "created_at": claim["created_at"],
            "updated_at": claim["updated_at"],
            "expenses": expenses,
        }

    def audit_events_for_claim(self, actor: ActorContext, claim_id: str) -> list[dict[str, object]]:
        self._claim_for_actor(actor, claim_id)
        return self.audit.list_for_entity(agency_id=actor.agency_id, entity_type="claim", entity_id=claim_id)

    def _validate_claim(self, claim_id: str) -> dict[str, object]:
        errors: list[dict[str, str]] = []
        expenses = self._expenses_for_claim(claim_id)
        if not expenses:
            errors.append({"field": "expenses", "issue": "at least one expense is required"})
            return {"valid": False, "errors": errors}
        for index, expense in enumerate(expenses):
            prefix = f"expenses[{index}]"
            for field in ("claimant", "date_of_service", "expense_category", "service_type"):
                if not expense[field]:
                    errors.append({"field": f"{prefix}.{field}", "issue": "is required"})
            if expense["requested_reimbursement_cents"] <= 0:
                errors.append({"field": f"{prefix}.requested_reimbursement_amount", "issue": "must be greater than 0"})
            if expense["requested_reimbursement_cents"] > expense["amount_charged_cents"]:
                errors.append(
                    {
                        "field": f"{prefix}.requested_reimbursement_amount",
                        "issue": "must not exceed amount_charged",
                    }
                )
            if expense["documentation_required"] and not self._documents_for_expense(expense["id"]):
                errors.append({"field": f"{prefix}.documents", "issue": "at least one supporting document is required"})
        return {"valid": not errors, "errors": errors}

    def _claim_for_employee_edit(self, actor: ActorContext, claim_id: str) -> sqlite3.Row:
        self._require_employee_actor(actor)
        claim = self._claim_for_actor(actor, claim_id)
        if claim["status"] != DRAFT:
            raise ConflictError("A non-draft claim cannot be edited in this slice")
        return claim

    def _claim_for_actor(self, actor: ActorContext, claim_id: str) -> sqlite3.Row:
        claim = self.conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
        if claim is None:
            raise NotFoundError("Claim not found")
        if claim["agency_id"] != actor.agency_id:
            raise ForbiddenError("Claim is outside actor agency")
        if actor.actor_type == "employee" and claim["employee_id"] != actor.actor_id:
            raise ForbiddenError("Employees can only access their own claims")
        return claim

    def _employee(self, employee_id: str) -> sqlite3.Row:
        employee = self.conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if employee is None:
            raise NotFoundError("Employee not found")
        return employee

    def _expense(self, expense_id: str) -> sqlite3.Row:
        expense = self.conn.execute("SELECT * FROM claim_expenses WHERE id = ?", (expense_id,)).fetchone()
        if expense is None:
            raise NotFoundError("Expense not found")
        return expense

    def _document(self, document_id: str) -> sqlite3.Row:
        document = self.conn.execute("SELECT * FROM claim_documents WHERE id = ?", (document_id,)).fetchone()
        if document is None:
            raise NotFoundError("Document not found")
        return document

    def _expenses_for_claim(self, claim_id: str) -> list[sqlite3.Row]:
        return list(
            self.conn.execute("SELECT * FROM claim_expenses WHERE claim_id = ? ORDER BY created_at, id", (claim_id,)).fetchall()
        )

    def _documents_for_expense(self, expense_id: str) -> list[sqlite3.Row]:
        return list(
            self.conn.execute("SELECT * FROM claim_documents WHERE expense_id = ? ORDER BY created_at, id", (expense_id,)).fetchall()
        )

    def _expense_response(self, expense: sqlite3.Row) -> dict[str, object]:
        return {
            "id": expense["id"],
            "claim_id": expense["claim_id"],
            "claimant": expense["claimant"],
            "date_of_service": expense["date_of_service"],
            "expense_category": expense["expense_category"],
            "amount_charged": self._format_cents(expense["amount_charged_cents"]),
            "requested_reimbursement_amount": self._format_cents(expense["requested_reimbursement_cents"]),
            "service_type": expense["service_type"],
            "documentation_required": bool(expense["documentation_required"]),
            "documents": [self._document_response(row) for row in self._documents_for_expense(expense["id"])],
        }

    @staticmethod
    def _document_response(document: sqlite3.Row) -> dict[str, object]:
        return {
            "id": document["id"],
            "claim_id": document["claim_id"],
            "expense_id": document["expense_id"],
            "file_name": document["file_name"],
            "mime_type": document["mime_type"],
            "size_bytes": document["size_bytes"],
            "checksum_sha256": document["checksum_sha256"],
            "document_type": document["document_type"],
            "created_at": document["created_at"],
        }

    @staticmethod
    def _required_str(payload: dict[str, object], field: str) -> str:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(details=[{"field": field, "issue": "is required"}])
        return value.strip()

    @staticmethod
    def _required_int(payload: dict[str, object], field: str) -> int:
        value = payload.get(field)
        if not isinstance(value, int):
            raise ValidationError(details=[{"field": field, "issue": "must be an integer"}])
        return value

    @classmethod
    def _required_date(cls, payload: dict[str, object], field: str) -> str:
        value = cls._required_str(payload, field)
        if not DATE_PATTERN.match(value):
            raise ValidationError(details=[{"field": field, "issue": "must use YYYY-MM-DD"}])
        return value

    @classmethod
    def _required_money_cents(cls, payload: dict[str, object], field: str) -> int:
        value = payload.get(field)
        if isinstance(value, int):
            return value * 100
        if isinstance(value, float):
            raise ValidationError(details=[{"field": field, "issue": "must be a decimal string"}])
        if not isinstance(value, str) or not MONEY_PATTERN.match(value):
            raise ValidationError(details=[{"field": field, "issue": "must be a decimal string"}])
        dollars, _, cents = value.partition(".")
        return int(dollars) * 100 + int((cents + "00")[:2])

    @staticmethod
    def _format_cents(cents: int) -> str:
        return f"{cents // 100}.{cents % 100:02d}"

    @staticmethod
    def _documentation_required(payload: dict[str, object], expense_category: str, service_type: str) -> bool:
        explicit_no_documentation = (
            expense_category.lower() in DOCUMENTATION_NOT_REQUIRED_TYPES
            or service_type.lower() in DOCUMENTATION_NOT_REQUIRED_TYPES
        )
        requested_value = payload.get("documentation_required", True)
        if requested_value is False and not explicit_no_documentation:
            raise ValidationError(
                details=[
                    {
                        "field": "documentation_required",
                        "issue": "can only be false for a documentation-not-required expense or service type",
                    }
                ]
            )
        return not explicit_no_documentation

    @staticmethod
    def _require_employee_actor(actor: ActorContext) -> None:
        if actor.actor_type != "employee":
            raise ForbiddenError("Only employee actions are supported in this slice")
