from typing import Any

from mem_resolve_app.mcp_client.client import (
    call_local_mcp_tool_sync,
)
from mem_resolve_app.tool_gateway.context import get_tool_context
from mem_resolve_app.tool_gateway.gateway import execute_tool


def _get_request_from_mcp(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an approval request through MCP."""
    return call_local_mcp_tool_sync(
        tool_name="get_approval_request",
        arguments={
            "request_id": request_id,
        },
    )


def get_request_for_review(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an approval request for human review.

    Args:
        request_id: Unique approval request identifier.

    Returns:
        Approval request details with a gateway correlation ID.
    """
    context = get_tool_context(
        agent_name="reviewer_agent",
    )

    gateway_response = execute_tool(
        tool_name="get_approval_request",
        context=context,
        handler=_get_request_from_mcp,
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


def _approve_through_mcp(
    request_id: str,
    reviewed_by: str,
    review_comment: str,
) -> dict[str, Any]:
    """Approve a request through MCP."""
    return call_local_mcp_tool_sync(
        tool_name="approve_request",
        arguments={
            "request_id": request_id,
            "reviewed_by": reviewed_by,
            "review_comment": review_comment,
        },
    )


def approve_request(
    request_id: str,
    reviewed_by: str,
    review_comment: str,
) -> dict[str, Any]:
    """Approve a pending request through the Tool Gateway.

    Args:
        request_id: Unique approval request identifier.
        reviewed_by: Human reviewer identity.
        review_comment: Evidence-based approval explanation.

    Returns:
        The review result with a gateway correlation ID.
    """
    context = get_tool_context(
        agent_name="reviewer_agent",
    )

    gateway_response = execute_tool(
        tool_name="approve_request",
        context=context,
        handler=_approve_through_mcp,
        arguments={
            "request_id": request_id,
            "reviewed_by": reviewed_by,
            "review_comment": review_comment,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    return {
        **gateway_response["result"],
        "correlation_id": gateway_response["correlation_id"],
    }


def _reject_through_mcp(
    request_id: str,
    reviewed_by: str,
    review_comment: str,
) -> dict[str, Any]:
    """Reject a request through MCP."""
    return call_local_mcp_tool_sync(
        tool_name="reject_request",
        arguments={
            "request_id": request_id,
            "reviewed_by": reviewed_by,
            "review_comment": review_comment,
        },
    )


def reject_request(
    request_id: str,
    reviewed_by: str,
    review_comment: str,
) -> dict[str, Any]:
    """Reject a pending request through the Tool Gateway.

    Args:
        request_id: Unique approval request identifier.
        reviewed_by: Human reviewer identity.
        review_comment: Evidence-based rejection explanation.

    Returns:
        The review result with a gateway correlation ID.
    """
    context = get_tool_context(
        agent_name="reviewer_agent",
    )

    gateway_response = execute_tool(
        tool_name="reject_request",
        context=context,
        handler=_reject_through_mcp,
        arguments={
            "request_id": request_id,
            "reviewed_by": reviewed_by,
            "review_comment": review_comment,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    return {
        **gateway_response["result"],
        "correlation_id": gateway_response["correlation_id"],
    }