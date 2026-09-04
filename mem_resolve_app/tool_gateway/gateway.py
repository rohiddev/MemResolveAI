from collections.abc import Callable
from time import perf_counter
from typing import Any

from mem_resolve_app.repositories.audit_repository import (
    write_audit_event,
)
from mem_resolve_app.tool_gateway.context import ToolRequestContext
from mem_resolve_app.tool_gateway.registry import (
    ToolRegistration,
    get_tool_registration,
)


ToolHandler = Callable[..., Any]


def _has_allowed_role(
    context: ToolRequestContext,
    registration: ToolRegistration,
) -> bool:
    return bool(
        set(context.roles).intersection(registration.allowed_roles)
    )


def execute_tool(
    *,
    tool_name: str,
    context: ToolRequestContext,
    handler: ToolHandler,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Validate, execute, and audit a tool request."""
    started_at = perf_counter()
    registration = get_tool_registration(tool_name)

    if registration is None:
        duration_ms = (perf_counter() - started_at) * 1000

        write_audit_event(
            correlation_id=context.correlation_id,
            tool_name=tool_name,
            agent_name=context.agent_name,
            user_id=context.user_id,
            outcome="BLOCKED_UNREGISTERED_TOOL",
            duration_ms=duration_ms,
        )

        return {
            "status": "FORBIDDEN",
            "message": f"Tool {tool_name} is not registered.",
            "correlation_id": context.correlation_id,
        }

    if context.agent_name not in registration.allowed_agents:
        duration_ms = (perf_counter() - started_at) * 1000

        write_audit_event(
            correlation_id=context.correlation_id,
            tool_name=tool_name,
            agent_name=context.agent_name,
            user_id=context.user_id,
            outcome="BLOCKED_AGENT",
            duration_ms=duration_ms,
        )

        return {
            "status": "FORBIDDEN",
            "message": (
                f"Agent {context.agent_name} is not allowed to use "
                f"tool {tool_name}."
            ),
            "correlation_id": context.correlation_id,
        }

    if not _has_allowed_role(context, registration):
        duration_ms = (perf_counter() - started_at) * 1000

        write_audit_event(
            correlation_id=context.correlation_id,
            tool_name=tool_name,
            agent_name=context.agent_name,
            user_id=context.user_id,
            outcome="BLOCKED_ROLE",
            duration_ms=duration_ms,
        )

        return {
            "status": "FORBIDDEN",
            "message": "The user does not have an allowed role.",
            "correlation_id": context.correlation_id,
        }

    try:
        result = handler(**arguments)
        duration_ms = (perf_counter() - started_at) * 1000

        write_audit_event(
            correlation_id=context.correlation_id,
            tool_name=tool_name,
            agent_name=context.agent_name,
            user_id=context.user_id,
            outcome="SUCCEEDED",
            duration_ms=duration_ms,
            details={
                "argument_names": sorted(arguments.keys()),
            },
        )

        return {
            "status": "SUCCEEDED",
            "correlation_id": context.correlation_id,
            "result": result,
        }

    except Exception as error:
        duration_ms = (perf_counter() - started_at) * 1000

        write_audit_event(
            correlation_id=context.correlation_id,
            tool_name=tool_name,
            agent_name=context.agent_name,
            user_id=context.user_id,
            outcome="FAILED",
            duration_ms=duration_ms,
            details={
                "error_type": type(error).__name__,
            },
        )

        return {
            "status": "ERROR",
            "message": "The tool request failed.",
            "error_type": type(error).__name__,
            "correlation_id": context.correlation_id,
        }