from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse

from .audit import ActorContext
from .errors import ApiError, NotFoundError, ValidationError
from .service import ClaimService

CLAIM_ID = r"(?P<claim_id>[^/]+)"
EXPENSE_ID = r"(?P<expense_id>[^/]+)"


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: dict[str, Any]


class ApiApp:
    def __init__(self, claim_service: ClaimService):
        self.claim_service = claim_service

    def handle(self, method: str, path: str, headers: dict[str, str] | None = None, body: str | bytes | None = None) -> ApiResponse:
        headers = headers or {}
        correlation_id = headers.get("X-Correlation-Id") or headers.get("x-correlation-id")
        try:
            actor = self._actor_from_headers(headers)
            parsed = urlparse(path)
            route_path = parsed.path
            payload = self._json_body(body)
            if method == "POST" and route_path == "/api/v1/claims":
                return ApiResponse(201, self.claim_service.create_claim(actor, payload, correlation_id))
            if method == "GET":
                match = re.fullmatch(rf"/api/v1/claims/{CLAIM_ID}", route_path)
                if match:
                    return ApiResponse(200, self.claim_service.get_claim(actor, match.group("claim_id")))
            if method == "POST":
                match = re.fullmatch(rf"/api/v1/claims/{CLAIM_ID}/expenses", route_path)
                if match:
                    return ApiResponse(
                        201,
                        self.claim_service.add_expense(actor, match.group("claim_id"), payload, correlation_id),
                    )
            if method == "POST":
                match = re.fullmatch(rf"/api/v1/claims/{CLAIM_ID}/expenses/{EXPENSE_ID}/documents", route_path)
                if match:
                    return ApiResponse(
                        201,
                        self.claim_service.attach_document(
                            actor,
                            match.group("claim_id"),
                            match.group("expense_id"),
                            payload,
                            correlation_id,
                        ),
                    )
            if method == "POST":
                match = re.fullmatch(rf"/api/v1/claims/{CLAIM_ID}/validate", route_path)
                if match:
                    return ApiResponse(200, self.claim_service.validate_claim(actor, match.group("claim_id"), correlation_id))
            if method == "POST":
                match = re.fullmatch(rf"/api/v1/claims/{CLAIM_ID}/submit", route_path)
                if match:
                    return ApiResponse(200, self.claim_service.submit_claim(actor, match.group("claim_id"), correlation_id))
            if method == "GET":
                match = re.fullmatch(rf"/api/v1/claims/{CLAIM_ID}/status", route_path)
                if match:
                    claim = self.claim_service.get_claim(actor, match.group("claim_id"))
                    return ApiResponse(200, {"claim_id": claim["id"], "status": claim["status"], "submitted_at": claim["submitted_at"]})
            if method == "GET" and route_path == "/api/v1/audit-events":
                query = parse_qs(parsed.query)
                entity_type = (query.get("entity_type") or ["claim"])[0]
                entity_id = (query.get("entity_id") or [""])[0]
                if not entity_id:
                    raise ValidationError(details=[{"field": "entity_id", "issue": "is required"}])
                events = self.claim_service.audit_events_for_claim(actor, entity_id) if entity_type == "claim" else []
                return ApiResponse(200, {"data": events})
            raise NotFoundError("Route not found")
        except ApiError as exc:
            return ApiResponse(exc.status, exc.envelope(correlation_id))

    @staticmethod
    def _json_body(body: str | bytes | None) -> dict[str, Any]:
        if body is None or body == b"" or body == "":
            return {}
        if isinstance(body, bytes):
            body = body.decode("utf-8")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            raise ValidationError(details=[{"field": "body", "issue": "must be valid JSON"}])
        if not isinstance(parsed, dict):
            raise ValidationError(details=[{"field": "body", "issue": "must be a JSON object"}])
        return parsed

    @staticmethod
    def _actor_from_headers(headers: dict[str, str]) -> ActorContext:
        normalized = {key.lower(): value for key, value in headers.items()}
        actor_type = normalized.get("x-actor-type")
        actor_id = normalized.get("x-actor-id")
        agency_id = normalized.get("x-agency-id")
        missing = [
            name
            for name, value in (("X-Actor-Type", actor_type), ("X-Actor-Id", actor_id), ("X-Agency-Id", agency_id))
            if not value
        ]
        if missing:
            raise ValidationError("Missing actor context", [{"field": name, "issue": "is required"} for name in missing])
        return ActorContext(actor_type=str(actor_type), actor_id=str(actor_id), agency_id=str(agency_id))
