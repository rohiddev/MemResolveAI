from typing import Any

from mem_resolve_app.mcp_client.client import (
    call_local_mcp_tool_sync,
)
from mem_resolve_app.tool_gateway.context import get_tool_context
from mem_resolve_app.tool_gateway.gateway import execute_tool


def _check_eligibility_through_mcp(
    member_id: str,
    service_date: str,
) -> dict[str, Any]:
    """Check eligibility through the MCP server.

    This private handler runs only after the Tool Gateway authorizes
    the request.
    """
    return call_local_mcp_tool_sync(
        tool_name="check_eligibility",
        arguments={
            "member_id": member_id,
            "service_date": service_date,
        },
    )


def check_eligibility(
    member_id: str,
    service_date: str,
) -> dict[str, Any]:
    """Check member eligibility through the Tool Gateway.

    Args:
        member_id: Member identifier such as MBR-1001.
        service_date: Service date in YYYY-MM-DD format.

    Returns:
        Eligibility information returned by the MCP server with
        a gateway correlation ID.
    """
    context = get_tool_context(
        agent_name="eligibility_agent",
    )

    gateway_response = execute_tool(
        tool_name="check_eligibility",
        context=context,
        handler=_check_eligibility_through_mcp,
        arguments={
            "member_id": member_id,
            "service_date": service_date,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    result = gateway_response["result"]

    return {
        **result,
        "correlation_id": gateway_response["correlation_id"],
    }