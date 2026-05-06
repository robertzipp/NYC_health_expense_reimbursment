from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.parse import parse_qs, urlparse

from .audit import ActorContext
from .service import ConflictError, ForbiddenError, NotFoundError, ServiceError


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: Any


class ApiApp:
    def __init__(self, service):
        self.service = service

    def handle(self, method: str, path: str, headers: dict[str, str], body: str | None = None) -> ApiResponse:
        try:
            actor = self._actor(headers)
            parsed = urlparse(path)
            segments = [segment for segment in parsed.path.strip("/").split("/") if segment]
            payload = self._payload(body)

            if segments == ["api", "v1", "claims"] and method == "POST":
                return ApiResponse(201, self.service.create_claim(actor, payload))

            if len(segments) == 4 and segments[:3] == ["api", "v1", "claims"] and method == "GET":
                return ApiResponse(200, self.service.get_claim(actor, segments[3]))

            if len(segments) == 5 and segments[:3] == ["api", "v1", "claims"] and segments[4] == "expenses" and method == "POST":
                details = self._validate_expense_boundary(payload)
                if details:
                    return self._error(400, "VALIDATION_ERROR", details)
                return ApiResponse(201, self.service.add_expense(actor, segments[3], payload))

            if len(segments) == 7 and segments[:3] == ["api", "v1", "claims"] and segments[4] == "expenses" and segments[6] == "documents" and method == "POST":
                return ApiResponse(201, self.service.attach_document(actor, segments[3], segments[5], payload))

            if len(segments) == 5 and segments[:3] == ["api", "v1", "claims"] and segments[4] == "validate" and method == "POST":
                return ApiResponse(200, self.service.validate_claim(actor, segments[3]))

            if len(segments) == 5 and segments[:3] == ["api", "v1", "claims"] and segments[4] == "submit" and method == "POST":
                return ApiResponse(200, self.service.submit_claim(actor, segments[3]))

            if segments == ["api", "v1", "receipts"] and method == "POST":
                return ApiResponse(201, self.service.create_receipt(actor, payload))

            if segments == ["api", "v1", "receipts"] and method == "GET":
                query = parse_qs(parsed.query)
                include_archived = query.get("include_archived", ["false"])[0].lower() == "true"
                return ApiResponse(200, {"data": self.service.list_receipts(actor, include_archived)})

            if len(segments) == 4 and segments[:3] == ["api", "v1", "receipts"] and method in {"PATCH", "PUT"}:
                return ApiResponse(200, self.service.update_receipt(actor, segments[3], payload))

            if len(segments) == 5 and segments[:3] == ["api", "v1", "receipts"] and segments[4] == "archive" and method == "POST":
                return ApiResponse(200, self.service.archive_receipt(actor, segments[3]))

            if len(segments) == 8 and segments[:3] == ["api", "v1", "claims"] and segments[4] == "expenses" and segments[6] == "saved-receipts" and method == "POST":
                return ApiResponse(201, self.service.attach_receipt_to_expense(actor, segments[3], segments[5], segments[7]))

            if segments == ["api", "v1", "audit-events"] and method == "GET":
                query = parse_qs(parsed.query)
                entity_type = query.get("entity_type", [""])[0]
                entity_id = query.get("entity_id", [""])[0]
                return ApiResponse(200, {"data": self.service.audit_events_for_entity(actor, entity_type, entity_id)})

            return self._error(404, "NOT_FOUND", [])
        except ServiceError as exc:
            return self._error(exc.status, exc.code, exc.details, exc.message)

    def _actor(self, headers: dict[str, str]) -> ActorContext:
        required = ["X-Actor-Type", "X-Actor-Id", "X-Agency-Id"]
        for header in required:
            if not headers.get(header):
                raise ServiceError(400, "VALIDATION_ERROR", [{"field": header, "issue": "is required"}])
        return ActorContext(headers["X-Actor-Type"], headers["X-Actor-Id"], headers["X-Agency-Id"], headers.get("X-Correlation-Id"))

    def _payload(self, body: str | None) -> dict[str, Any]:
        if body is None or body == "":
            return {}
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise ServiceError(400, "VALIDATION_ERROR", [{"field": "body", "issue": "must be valid JSON"}])
        if not isinstance(payload, dict):
            raise ServiceError(400, "VALIDATION_ERROR", [{"field": "body", "issue": "must be a JSON object"}])
        return payload

    def _validate_expense_boundary(self, payload: dict[str, Any]) -> list[dict[str, str]]:
        details: list[dict[str, str]] = []
        for field in ("amount_charged", "requested_reimbursement_amount"):
            if field in payload and not isinstance(payload[field], str):
                details.append({"field": field, "issue": "must be a decimal string"})
        if "date_of_service" in payload:
            try:
                date.fromisoformat(str(payload["date_of_service"]))
            except ValueError:
                details.append({"field": "date_of_service", "issue": "must be a valid calendar date"})
        return details

    def _error(self, status: int, code: str, details: list[dict[str, str]], message: str | None = None) -> ApiResponse:
        messages = {
            "VALIDATION_ERROR": "Request validation failed.",
            "BUSINESS_RULE_VIOLATION": "Claim cannot be submitted.",
            "NOT_FOUND": "Resource was not found.",
            "FORBIDDEN": "Actor is not allowed to access this resource.",
            "CONFLICT": "Requested state transition is not allowed.",
        }
        return ApiResponse(status, {"error": {"code": code, "message": message or messages.get(code, "Request failed."), "details": details}})
