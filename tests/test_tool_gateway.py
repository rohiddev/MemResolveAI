from typing import Any

from mem_resolve_app.tool_gateway import gateway
from mem_resolve_app.tool_gateway.context import ToolRequestContext


def create_context(
    *,
    agent_name: str = "claim_agent",
    roles: tuple[str, ...] = ("provider_ops",),
) -> ToolRequestContext:
    return ToolRequestContext(
        correlation_id="correlation-test-001",
        user_id="user-test-001",
        agent_name=agent_name,
        roles=roles,
    )


def capture_audit_events(
    monkeypatch,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    def write_event(**event: Any) -> str:
        events.append(event)
        return "audit-test-001"

    monkeypatch.setattr(
        gateway,
        "write_audit_event",
        write_event,
    )

    return events


def test_registered_tool_executes_for_authorized_agent_and_role(
    monkeypatch,
) -> None:
    audit_events = capture_audit_events(monkeypatch)

    result = gateway.execute_tool(
        tool_name="get_claim",
        context=create_context(),
        handler=lambda claim_id: {
            "claim_id": claim_id,
            "status": "FOUND",
        },
        arguments={
            "claim_id": "CLM-20045",
        },
    )

    assert result == {
        "status": "SUCCEEDED",
        "correlation_id": "correlation-test-001",
        "result": {
            "claim_id": "CLM-20045",
            "status": "FOUND",
        },
    }

    assert len(audit_events) == 1

    audit_event = audit_events[0]
    assert audit_event["outcome"] == "SUCCEEDED"
    assert audit_event["tool_name"] == "get_claim"
    assert audit_event["agent_name"] == "claim_agent"
    assert audit_event["user_id"] == "user-test-001"
    assert audit_event["details"] == {
        "argument_names": ["claim_id"],
    }
    assert audit_event["duration_ms"] >= 0


def test_unregistered_tool_is_blocked_and_audited(
    monkeypatch,
) -> None:
    audit_events = capture_audit_events(monkeypatch)

    handler_called = False

    def handler() -> None:
        nonlocal handler_called
        handler_called = True

    result = gateway.execute_tool(
        tool_name="delete_claim",
        context=create_context(),
        handler=handler,
        arguments={},
    )

    assert result == {
        "status": "FORBIDDEN",
        "message": "Tool delete_claim is not registered.",
        "correlation_id": "correlation-test-001",
    }
    assert handler_called is False
    assert len(audit_events) == 1
    assert (
        audit_events[0]["outcome"]
        == "BLOCKED_UNREGISTERED_TOOL"
    )


def test_tool_is_blocked_for_unauthorized_agent(
    monkeypatch,
) -> None:
    audit_events = capture_audit_events(monkeypatch)

    result = gateway.execute_tool(
        tool_name="get_claim",
        context=create_context(
            agent_name="eligibility_agent",
        ),
        handler=lambda claim_id: {
            "claim_id": claim_id,
        },
        arguments={
            "claim_id": "CLM-20045",
        },
    )

    assert result["status"] == "FORBIDDEN"
    assert result["message"] == (
        "Agent eligibility_agent is not allowed to use "
        "tool get_claim."
    )
    assert len(audit_events) == 1
    assert audit_events[0]["outcome"] == "BLOCKED_AGENT"


def test_tool_is_blocked_for_unauthorized_role(
    monkeypatch,
) -> None:
    audit_events = capture_audit_events(monkeypatch)

    result = gateway.execute_tool(
        tool_name="get_claim",
        context=create_context(
            roles=("unapproved_role",),
        ),
        handler=lambda claim_id: {
            "claim_id": claim_id,
        },
        arguments={
            "claim_id": "CLM-20045",
        },
    )

    assert result == {
        "status": "FORBIDDEN",
        "message": "The user does not have an allowed role.",
        "correlation_id": "correlation-test-001",
    }
    assert len(audit_events) == 1
    assert audit_events[0]["outcome"] == "BLOCKED_ROLE"


def test_handler_failure_is_controlled_and_audited(
    monkeypatch,
) -> None:
    audit_events = capture_audit_events(monkeypatch)

    def failing_handler(
        claim_id: str,
    ) -> dict[str, Any]:
        del claim_id
        raise ValueError("Sensitive internal failure details")

    result = gateway.execute_tool(
        tool_name="get_claim",
        context=create_context(),
        handler=failing_handler,
        arguments={
            "claim_id": "CLM-20045",
        },
    )

    assert result == {
        "status": "ERROR",
        "message": "The tool request failed.",
        "error_type": "ValueError",
        "correlation_id": "correlation-test-001",
    }

    # Internal exception text must not be exposed to the caller.
    assert "Sensitive internal failure details" not in str(result)

    assert len(audit_events) == 1

    audit_event = audit_events[0]
    assert audit_event["outcome"] == "FAILED"
    assert audit_event["details"] == {
        "error_type": "ValueError",
    }