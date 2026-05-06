from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from .audit import ActorContext

SUPPORTED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")


class ServiceError(Exception):
    def __init__(self, status: int, code: str, details: list[dict[str, str]], message: str = "Request validation failed."):
        super().__init__(message)
        self.status = status
        self.code = code
        self.details = details
        self.message = message


class NotFoundError(ServiceError):
    def __init__(self, message: str = "Resource was not found."):
        super().__init__(404, "NOT_FOUND", [], message)


class ForbiddenError(ServiceError):
    def __init__(self, message: str = "Actor is not allowed to access this resource."):
        super().__init__(403, "FORBIDDEN", [], message)


class ConflictError(ServiceError):
    def __init__(self, message: str = "Requested state transition is not allowed."):
        super().__init__(409, "CONFLICT", [], message)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def cents(value: Any, field: str, details: list[dict[str, str]]) -> int:
    if not isinstance(value, str):
        details.append({"field": field, "issue": "must be a decimal string"})
        return 0
    try:
        amount = Decimal(value)
    except InvalidOperation:
        details.append({"field": field, "issue": "must be a decimal string"})
        return 0
    if amount <= 0:
        details.append({"field": field, "issue": "must be greater than 0"})
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def iso(row_value: Any) -> str | None:
    return None if row_value is None else str(row_value)


class ClaimService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_claim(self, actor: ActorContext, request: dict[str, Any]) -> dict[str, Any]:
        employee_id = clean(request.get("employee_id"))
        if not employee_id:
            raise ServiceError(400, "VALIDATION_ERROR", [{"field": "employee_id", "issue": "is required"}])
        if actor.actor_type == "employee" and actor.actor_id != employee_id:
            raise ForbiddenError()
        claim_id = str(uuid.uuid4())
        created_at = now()
        self.conn.execute(
            "INSERT INTO claims (id, agency_id, employee_id, status, created_at) VALUES (?, ?, ?, 'Draft', ?)",
            (claim_id, actor.agency_id, employee_id, created_at),
        )
        self._audit(actor, "claim.created", "success", "claim", claim_id, {"employee_id": employee_id})
        self.conn.commit()
        return self.get_claim(actor, claim_id)

    def get_claim(self, actor: ActorContext, claim_id: str) -> dict[str, Any]:
        claim = self._claim_row(claim_id)
        self._require_claim_access(actor, claim)
        return self._claim_dict(claim)

    def add_expense(self, actor: ActorContext, claim_id: str, request: dict[str, Any]) -> dict[str, Any]:
        claim = self._require_draft_claim(actor, claim_id)
        details = validate_expense(request)
        if details:
            raise ServiceError(400, "VALIDATION_ERROR", details)
        expense_id = str(uuid.uuid4())
        self.conn.execute(
            """
            INSERT INTO claim_expenses (
                id, claim_id, claimant, date_of_service, expense_category,
                amount_charged_cents, requested_reimbursement_cents, service_type, documentation_required, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                expense_id,
                claim_id,
                clean(request.get("claimant")),
                request["date_of_service"],
                clean(request.get("expense_category")),
                cents(request.get("amount_charged"), "amount_charged", []),
                cents(request.get("requested_reimbursement_amount"), "requested_reimbursement_amount", []),
                clean(request.get("service_type")),
                1 if request.get("documentation_required", True) else 0,
                now(),
            ),
        )
        self._audit(actor, "claim_expense.added", "success", "claim", claim_id, {"expense_id": expense_id})
        self.conn.commit()
        return self._expense_dict(self.conn.execute("SELECT * FROM claim_expenses WHERE id = ?", (expense_id,)).fetchone())

    def attach_document(self, actor: ActorContext, claim_id: str, expense_id: str, request: dict[str, Any]) -> dict[str, Any]:
        self._require_draft_claim(actor, claim_id)
        self._expense_row(claim_id, expense_id)
        if not request.get("checksum_sha256"):
            request = {**request, "checksum_sha256": "0" * 64}
        details = validate_document(request)
        if details:
            raise ServiceError(400, "VALIDATION_ERROR", details)
        document = self._insert_claim_document(actor, claim_id, expense_id, request, None)
        self._audit(actor, "claim_document.attached", "success", "claim", claim_id, {"expense_id": expense_id, "document_id": document["id"]})
        self.conn.commit()
        return document

    def create_receipt(self, actor: ActorContext, request: dict[str, Any]) -> dict[str, Any]:
        details = validate_document(request)
        if details:
            raise ServiceError(400, "VALIDATION_ERROR", details)
        receipt_id = str(uuid.uuid4())
        timestamp = now()
        self.conn.execute(
            """
            INSERT INTO saved_receipts (
                id, agency_id, employee_id, file_name, mime_type, size_bytes, checksum_sha256,
                document_type, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available', ?, ?)
            """,
            (
                receipt_id,
                actor.agency_id,
                actor.actor_id,
                clean(request.get("file_name")),
                clean(request.get("mime_type")).lower(),
                int(request.get("size_bytes")),
                clean(request.get("checksum_sha256")).lower(),
                clean(request.get("document_type")),
                clean(request.get("description")) or None,
                timestamp,
                timestamp,
            ),
        )
        self._audit(actor, "receipt.created", "success", "receipt", receipt_id, {"file_name": clean(request.get("file_name"))})
        self.conn.commit()
        return self._receipt_dict(self._receipt_row(receipt_id))

    def list_receipts(self, actor: ActorContext, include_archived: bool = False) -> list[dict[str, Any]]:
        sql = "SELECT * FROM saved_receipts WHERE agency_id = ? AND employee_id = ?"
        params: list[Any] = [actor.agency_id, actor.actor_id]
        if not include_archived:
            sql += " AND status != 'Archived'"
        sql += " ORDER BY created_at, id"
        return [self._receipt_dict(row) for row in self.conn.execute(sql, params).fetchall()]

    def update_receipt(self, actor: ActorContext, receipt_id: str, request: dict[str, Any]) -> dict[str, Any]:
        receipt = self._accessible_receipt(actor, receipt_id)
        if receipt["status"] != "Available":
            raise ConflictError("Only unattached available receipts can be updated.")
        merged = {**dict(receipt), **request}
        details = validate_document(merged)
        if details:
            raise ServiceError(400, "VALIDATION_ERROR", details)
        timestamp = now()
        self.conn.execute(
            """
            UPDATE saved_receipts
            SET file_name = ?, mime_type = ?, size_bytes = ?, checksum_sha256 = ?, document_type = ?, description = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                clean(merged.get("file_name")),
                clean(merged.get("mime_type")).lower(),
                int(merged.get("size_bytes")),
                clean(merged.get("checksum_sha256")).lower(),
                clean(merged.get("document_type")),
                clean(merged.get("description")) or None,
                timestamp,
                receipt_id,
            ),
        )
        self._audit(actor, "receipt.updated", "success", "receipt", receipt_id, {})
        self.conn.commit()
        return self._receipt_dict(self._receipt_row(receipt_id))

    def archive_receipt(self, actor: ActorContext, receipt_id: str) -> dict[str, Any]:
        receipt = self._accessible_receipt(actor, receipt_id)
        if receipt["status"] != "Available":
            raise ConflictError("Only unattached available receipts can be archived.")
        timestamp = now()
        self.conn.execute(
            "UPDATE saved_receipts SET status = 'Archived', updated_at = ?, archived_at = ? WHERE id = ?",
            (timestamp, timestamp, receipt_id),
        )
        self._audit(actor, "receipt.archived", "success", "receipt", receipt_id, {})
        self.conn.commit()
        return self._receipt_dict(self._receipt_row(receipt_id))

    def attach_receipt_to_expense(self, actor: ActorContext, claim_id: str, expense_id: str, receipt_id: str) -> dict[str, Any]:
        self._require_draft_claim(actor, claim_id)
        self._expense_row(claim_id, expense_id)
        receipt = self._accessible_receipt(actor, receipt_id)
        if receipt["status"] != "Available":
            raise ConflictError("Only unattached available receipts can be attached.")
        request = dict(receipt)
        document = self._insert_claim_document(actor, claim_id, expense_id, request, receipt_id)
        timestamp = now()
        self.conn.execute(
            """
            UPDATE saved_receipts
            SET status = 'Attached', claim_id = ?, expense_id = ?, attached_at = ?, updated_at = ?
            WHERE id = ?
            """,
            (claim_id, expense_id, timestamp, timestamp, receipt_id),
        )
        self._audit(actor, "receipt.attached", "success", "receipt", receipt_id, {"claim_id": claim_id, "expense_id": expense_id, "document_id": document["id"]})
        self._audit(actor, "claim_document.attached", "success", "claim", claim_id, {"expense_id": expense_id, "document_id": document["id"], "saved_receipt_id": receipt_id})
        self.conn.commit()
        return document

    def validate_claim(self, actor: ActorContext, claim_id: str) -> dict[str, Any]:
        claim = self.get_claim(actor, claim_id)
        details = self._submission_details(claim)
        return {"valid": not details, "details": details}

    def submit_claim(self, actor: ActorContext, claim_id: str) -> dict[str, Any]:
        claim_row = self._claim_row(claim_id)
        self._require_claim_access(actor, claim_row)
        if claim_row["status"] != "Draft":
            raise ConflictError("Claim cannot be submitted twice.")
        claim = self._claim_dict(claim_row)
        details = self._submission_details(claim)
        if details:
            self._audit(actor, "claim.validation_failed", "failure", "claim", claim_id, {"details": details})
            self.conn.commit()
            raise ServiceError(422, "BUSINESS_RULE_VIOLATION", details, "Claim cannot be submitted.")
        submitted_at = now()
        self.conn.execute("UPDATE claims SET status = 'Submitted', submitted_at = ? WHERE id = ?", (submitted_at, claim_id))
        self._audit(actor, "claim.submitted", "success", "claim", claim_id, {"submitted_at": submitted_at})
        self.conn.commit()
        return self.get_claim(actor, claim_id)

    def audit_events_for_claim(self, actor: ActorContext, claim_id: str) -> list[dict[str, Any]]:
        claim = self._claim_row(claim_id)
        self._require_claim_access(actor, claim)
        return self._audit_events("claim", claim_id)

    def audit_events_for_entity(self, actor: ActorContext, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        if entity_type == "claim":
            return self.audit_events_for_claim(actor, entity_id)
        if entity_type == "receipt":
            self._accessible_receipt(actor, entity_id)
            return self._audit_events("receipt", entity_id)
        raise NotFoundError()

    def _insert_claim_document(self, actor: ActorContext, claim_id: str, expense_id: str, request: dict[str, Any], receipt_id: str | None) -> dict[str, Any]:
        document_id = str(uuid.uuid4())
        attached_at = now()
        self.conn.execute(
            """
            INSERT INTO claim_documents (
                id, claim_id, expense_id, saved_receipt_id, file_name, mime_type, size_bytes,
                checksum_sha256, document_type, attached_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                claim_id,
                expense_id,
                receipt_id,
                clean(request.get("file_name")),
                clean(request.get("mime_type")).lower(),
                int(request.get("size_bytes")),
                clean(request.get("checksum_sha256")).lower(),
                clean(request.get("document_type")),
                attached_at,
            ),
        )
        return self._document_dict(self.conn.execute("SELECT * FROM claim_documents WHERE id = ?", (document_id,)).fetchone())

    def _claim_row(self, claim_id: str) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM claims WHERE id = ?", (claim_id,)).fetchone()
        if row is None:
            raise NotFoundError("Claim was not found.")
        return row

    def _expense_row(self, claim_id: str, expense_id: str) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM claim_expenses WHERE claim_id = ? AND id = ?", (claim_id, expense_id)).fetchone()
        if row is None:
            raise NotFoundError("Expense was not found on this claim.")
        return row

    def _receipt_row(self, receipt_id: str) -> sqlite3.Row:
        row = self.conn.execute("SELECT * FROM saved_receipts WHERE id = ?", (receipt_id,)).fetchone()
        if row is None:
            raise NotFoundError("Receipt was not found.")
        return row

    def _accessible_receipt(self, actor: ActorContext, receipt_id: str) -> sqlite3.Row:
        receipt = self._receipt_row(receipt_id)
        if receipt["agency_id"] != actor.agency_id or (actor.actor_type == "employee" and receipt["employee_id"] != actor.actor_id):
            raise ForbiddenError()
        return receipt

    def _require_claim_access(self, actor: ActorContext, claim: sqlite3.Row) -> None:
        if claim["agency_id"] != actor.agency_id or (actor.actor_type == "employee" and claim["employee_id"] != actor.actor_id):
            raise ForbiddenError()

    def _require_draft_claim(self, actor: ActorContext, claim_id: str) -> sqlite3.Row:
        claim = self._claim_row(claim_id)
        self._require_claim_access(actor, claim)
        if claim["status"] != "Draft":
            raise ConflictError("A non-draft claim cannot be edited by the employee.")
        return claim

    def _claim_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        expenses = [self._expense_dict(exp) for exp in self.conn.execute("SELECT * FROM claim_expenses WHERE claim_id = ? ORDER BY created_at, id", (row["id"],)).fetchall()]
        return {"id": row["id"], "agency_id": row["agency_id"], "employee_id": row["employee_id"], "status": row["status"], "created_at": iso(row["created_at"]), "submitted_at": iso(row["submitted_at"]), "expenses": expenses}

    def _expense_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        documents = [self._document_dict(doc) for doc in self.conn.execute("SELECT * FROM claim_documents WHERE expense_id = ? ORDER BY attached_at, id", (row["id"],)).fetchall()]
        return {"id": row["id"], "claimant": row["claimant"], "date_of_service": row["date_of_service"], "expense_category": row["expense_category"], "amount_charged": f'{Decimal(row["amount_charged_cents"]) / 100:.2f}', "requested_reimbursement_amount": f'{Decimal(row["requested_reimbursement_cents"]) / 100:.2f}', "service_type": row["service_type"], "documentation_required": bool(row["documentation_required"]), "documents": documents}

    def _document_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {"id": row["id"], "expense_id": row["expense_id"], "saved_receipt_id": row["saved_receipt_id"], "file_name": row["file_name"], "mime_type": row["mime_type"], "size_bytes": row["size_bytes"], "checksum_sha256": row["checksum_sha256"], "document_type": row["document_type"], "attached_at": iso(row["attached_at"])}

    def _receipt_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        return {"id": row["id"], "agency_id": row["agency_id"], "employee_id": row["employee_id"], "file_name": row["file_name"], "mime_type": row["mime_type"], "size_bytes": row["size_bytes"], "checksum_sha256": row["checksum_sha256"], "document_type": row["document_type"], "description": row["description"], "status": row["status"], "claim_id": row["claim_id"], "expense_id": row["expense_id"], "created_at": iso(row["created_at"]), "updated_at": iso(row["updated_at"]), "attached_at": iso(row["attached_at"]), "archived_at": iso(row["archived_at"])}

    def _submission_details(self, claim: dict[str, Any]) -> list[dict[str, str]]:
        details: list[dict[str, str]] = []
        if not claim["expenses"]:
            details.append({"field": "expenses", "issue": "submitted claim must have at least one expense"})
        for expense in claim["expenses"]:
            if expense["documentation_required"] and not expense["documents"]:
                details.append({"field": f"expenses[{expense['id']}].documents", "issue": "supporting document is required for this expense"})
        return details

    def _audit(self, actor: ActorContext, event_type: str, outcome: str, entity_type: str, entity_id: str, data: dict[str, Any]) -> None:
        self.conn.execute(
            """
            INSERT INTO audit_events (id, event_type, outcome, entity_type, entity_id, actor_type, actor_id, agency_id, correlation_id, occurred_at, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), event_type, outcome, entity_type, entity_id, actor.actor_type, actor.actor_id, actor.agency_id, actor.correlation_id, now(), json.dumps(data, sort_keys=True)),
        )

    def _audit_events(self, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM audit_events WHERE entity_type = ? AND entity_id = ? ORDER BY occurred_at, id", (entity_type, entity_id)).fetchall()
        return [{"id": r["id"], "event_type": r["event_type"], "outcome": r["outcome"], "entity_type": r["entity_type"], "entity_id": r["entity_id"], "actor_type": r["actor_type"], "actor_id": r["actor_id"], "agency_id": r["agency_id"], "correlation_id": r["correlation_id"], "occurred_at": r["occurred_at"], "data": json.loads(r["data"])} for r in rows]


def validate_expense(request: dict[str, Any]) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    for field in ("claimant", "expense_category", "service_type"):
        if not clean(request.get(field)):
            details.append({"field": field, "issue": "is required"})
    amount = cents(request.get("amount_charged"), "amount_charged", details)
    requested = cents(request.get("requested_reimbursement_amount"), "requested_reimbursement_amount", details)
    if amount and requested and requested > amount:
        details.append({"field": "requested_reimbursement_amount", "issue": "must not exceed amount charged"})
    return details


def validate_document(request: dict[str, Any]) -> list[dict[str, str]]:
    details: list[dict[str, str]] = []
    file_name = clean(request.get("file_name"))
    if not file_name:
        details.append({"field": "file_name", "issue": "is required"})
    elif "/" in file_name or "\\" in file_name:
        details.append({"field": "file_name", "issue": "must be a file name without path segments"})
    mime_type = clean(request.get("mime_type")).lower()
    if mime_type not in SUPPORTED_MIME_TYPES:
        details.append({"field": "mime_type", "issue": "unsupported file type"})
    try:
        if int(request.get("size_bytes", 0)) <= 0:
            details.append({"field": "size_bytes", "issue": "must be greater than 0"})
    except (TypeError, ValueError):
        details.append({"field": "size_bytes", "issue": "must be greater than 0"})
    checksum = clean(request.get("checksum_sha256"))
    if not SHA256_RE.match(checksum):
        details.append({"field": "checksum_sha256", "issue": "must be a 64-character hexadecimal SHA-256"})
    if not clean(request.get("document_type")):
        details.append({"field": "document_type", "issue": "is required"})
    return details
