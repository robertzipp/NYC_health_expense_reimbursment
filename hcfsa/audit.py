from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActorContext:
    actor_type: str
    actor_id: str
    agency_id: str
    correlation_id: str | None = None
