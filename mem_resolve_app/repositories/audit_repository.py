from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from mem_resolve_app.repositories.firestore_client import (
    get_firestore_client,
)


COLLECTION_NAME = "memresolve_audit_events"


def write_audit_event(
    *,
    correlation_id: str,
    tool_name: str,
    agent_name: str,
    user_id: str,
    outcome: str,
    duration_ms: float,
    details: dict[str, Any] | None = None,
) -> str:
    """Write a tool audit event to Firestore."""
    client = get_firestore_client()
    event_id = str(uuid4())

    event = {
        "event_id": event_id,
        "correlation_id": correlation_id,
        "tool_name": tool_name,
        "agent_name": agent_name,
        "user_id": user_id,
        "outcome": outcome,
        "duration_ms": round(duration_ms, 2),
        "details": details or {},
        "created_at": datetime.now(UTC),
    }

    client.collection(COLLECTION_NAME).document(event_id).set(event)

    return event_id