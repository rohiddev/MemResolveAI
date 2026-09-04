from typing import Any

from mem_resolve_app.mcp_client.client import (
    call_local_mcp_tool_sync,
)
from mem_resolve_app.tool_gateway.context import get_tool_context
from mem_resolve_app.tool_gateway.gateway import execute_tool


def _create_approval_through_mcp(
    claim_id: str,
    action: str,
    reason: str,
    requested_by: str,
) -> dict[str, Any]:
    """Create an approval request through the MCP server.

    This private handler runs only after the Tool Gateway authorizes
    the request.
    """
    return call_local_mcp_tool_sync(
        tool_name="create_approval_request",
        arguments={
            "claim_id": claim_id,
            "action": action,
            "reason": reason,
            "requested_by": requested_by,
        },
    )


def create_approval_request(
    claim_id: str,
    action: str,
    reason: str,
    requested_by: str,
) -> dict[str, Any]:
    """Create a human approval request through the Tool Gateway.

    Args:
        claim_id: Claim identifier such as CLM-20045.
        action: REVIEW_CODE_MISMATCH, CORRECT_AND_RESUBMIT, or
            REQUEST_CLINICAL_REVIEW.
        reason: Evidence-based reason for the requested action.
        requested_by: Identity of the requesting user.

    Returns:
        The MCP approval result with a gateway correlation ID.
    """
    context = get_tool_context(
        agent_name="approval_agent",
    )

    gateway_response = execute_tool(
        tool_name="create_approval_request",
        context=context,
        handler=_create_approval_through_mcp,
        arguments={
            "claim_id": claim_id,
            "action": action,
            "reason": reason,
            "requested_by": requested_by,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    result = gateway_response["result"]

    return {
        **result,
        "correlation_id": gateway_response["correlation_id"],
    }


def _get_approval_through_mcp(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an approval request through the MCP server.

    This private handler runs only after the Tool Gateway authorizes
    the request.
    """
    return call_local_mcp_tool_sync(
        tool_name="get_approval_request",
        arguments={
            "request_id": request_id,
        },
    )


def get_approval_request(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an approval request through the Tool Gateway.

    Args:
        request_id: Unique approval request identifier.

    Returns:
        Approval information from MCP with a gateway correlation ID.
    """
    context = get_tool_context(
        agent_name="approval_agent",
    )

    gateway_response = execute_tool(
        tool_name="get_approval_request",
        context=context,
        handler=_get_approval_through_mcp,
        arguments={
            "request_id": request_id,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    result = gateway_response["result"]

    return {
        **result,
        "correlation_id": gateway_response["correlation_id"],
    }