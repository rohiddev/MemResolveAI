from typing import Any

from mem_resolve_app.mcp_client.client import (
    call_local_mcp_tool_sync,
)
from mem_resolve_app.tool_gateway.context import get_tool_context
from mem_resolve_app.tool_gateway.gateway import execute_tool


def _get_approval_from_mcp(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an approval request through the MCP server."""
    return call_local_mcp_tool_sync(
        tool_name="get_approval_request",
        arguments={
            "request_id": request_id,
        },
    )


def get_approval_for_execution(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an approval request before execution.

    Args:
        request_id: Unique approval request identifier.

    Returns:
        Approval information returned by MCP with a gateway
        correlation ID.
    """
    context = get_tool_context(
        agent_name="executor_agent",
    )

    gateway_response = execute_tool(
        tool_name="get_approval_request",
        context=context,
        handler=_get_approval_from_mcp,
        arguments={
            "request_id": request_id,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    return {
        **gateway_response["result"],
        "correlation_id": gateway_response["correlation_id"],
    }


def _execute_through_mcp(
    request_id: str,
    executed_by: str,
) -> dict[str, Any]:
    """Execute an approved request through the MCP server."""
    return call_local_mcp_tool_sync(
        tool_name="execute_approved_action",
        arguments={
            "request_id": request_id,
            "executed_by": executed_by,
        },
    )


def execute_approved_action(
    request_id: str,
    executed_by: str,
) -> dict[str, Any]:
    """Execute an approved action through the Tool Gateway.

    Args:
        request_id: Approved request identifier.
        executed_by: Identity of the authorized executor.

    Returns:
        Execution information returned by MCP with a gateway
        correlation ID.
    """
    context = get_tool_context(
        agent_name="executor_agent",
    )

    gateway_response = execute_tool(
        tool_name="execute_approved_action",
        context=context,
        handler=_execute_through_mcp,
        arguments={
            "request_id": request_id,
            "executed_by": executed_by,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    return {
        **gateway_response["result"],
        "correlation_id": gateway_response["correlation_id"],
    }


def _get_execution_from_mcp(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an execution record through the MCP server."""
    return call_local_mcp_tool_sync(
        tool_name="get_execution",
        arguments={
            "request_id": request_id,
        },
    )


def get_execution(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an execution record through the Tool Gateway.

    Args:
        request_id: Approval request identifier.

    Returns:
        Execution information returned by MCP with a gateway
        correlation ID.
    """
    context = get_tool_context(
        agent_name="executor_agent",
    )

    gateway_response = execute_tool(
        tool_name="get_execution",
        context=context,
        handler=_get_execution_from_mcp,
        arguments={
            "request_id": request_id,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    return {
        **gateway_response["result"],
        "correlation_id": gateway_response["correlation_id"],
    }