from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class ActorContext:
    actor_type: str
    actor_id: str
    agency_id: str


class AuditService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def record(
        self,
        *,
        actor: ActorContext,
        event_type: str,
        entity_type: str,
        entity_id: str,
        outcome: str = "success",
        correlation_id: str | None = None,
        details: dict[str, object] | None = None,
    ) -> str:
        occurred_at = datetime.now(timezone.utc).isoformat()
        previous_hash = self._last_hash(actor.agency_id)
        details_json = json.dumps(details or {}, sort_keys=True, separators=(",", ":"))
        event_id = str(uuid4())
        event_hash = self._hash_event(
            previous_hash,
            {
                "id": event_id,
                "occurred_at": occurred_at,
                "actor_type": actor.actor_type,
                "actor_id": actor.actor_id,
                "agency_id": actor.agency_id,
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "outcome": outcome,
                "correlation_id": correlation_id,
                "details_json": details_json,
            },
        )
        self.conn.execute(
            """
            INSERT INTO audit_events (
                id, occurred_at, actor_type, actor_id, agency_id, event_type, entity_type,
                entity_id, outcome, correlation_id, details_json, previous_hash, event_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                occurred_at,
                actor.actor_type,
                actor.actor_id,
                actor.agency_id,
                event_type,
                entity_type,
                entity_id,
                outcome,
                correlation_id,
                details_json,
                previous_hash,
                event_hash,
            ),
        )
        return event_id

    def list_for_entity(self, *, agency_id: str, entity_type: str, entity_id: str) -> list[dict[str, object]]:
        rows = self.conn.execute(
            """
            SELECT id, occurred_at, actor_type, actor_id, agency_id, event_type, entity_type,
                   entity_id, outcome, correlation_id, details_json, previous_hash, event_hash
            FROM audit_events
            WHERE agency_id = ? AND entity_type = ? AND entity_id = ?
            ORDER BY occurred_at, id
            """,
            (agency_id, entity_type, entity_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def _last_hash(self, agency_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT event_hash FROM audit_events WHERE agency_id = ? ORDER BY occurred_at DESC, id DESC LIMIT 1",
            (agency_id,),
        ).fetchone()
        return None if row is None else str(row["event_hash"])

    @staticmethod
    def _hash_event(previous_hash: str | None, payload: dict[str, object]) -> str:
        canonical = json.dumps(
            {"previous_hash": previous_hash, "payload": payload},
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
