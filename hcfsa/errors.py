from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApiError(Exception):
    code: str
    message: str
    status: int = 400
    details: list[dict[str, str]] | None = None

    def envelope(self, correlation_id: str | None = None) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details or [],
                "correlation_id": correlation_id,
            }
        }


class ValidationError(ApiError):
    def __init__(self, message: str = "Validation failed", details: list[dict[str, str]] | None = None):
        super().__init__("VALIDATION_ERROR", message, 400, details)


class ForbiddenError(ApiError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__("FORBIDDEN", message, 403, [])


class NotFoundError(ApiError):
    def __init__(self, message: str = "Not found"):
        super().__init__("NOT_FOUND", message, 404, [])


class ConflictError(ApiError):
    def __init__(self, message: str = "Conflict", details: list[dict[str, str]] | None = None):
        super().__init__("CONFLICT", message, 409, details)


class BusinessRuleViolation(ApiError):
    def __init__(self, message: str = "Business rule violation", details: list[dict[str, str]] | None = None):
        super().__init__("BUSINESS_RULE_VIOLATION", message, 422, details)
