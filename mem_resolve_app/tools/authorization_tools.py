from typing import Any

from mem_resolve_app.mcp_client.client import (
    call_local_mcp_tool_sync,
)
from mem_resolve_app.tool_gateway.context import get_tool_context
from mem_resolve_app.tool_gateway.gateway import execute_tool


def _retrieve_authorization_from_mcp(
    authorization_id: str,
) -> dict[str, Any]:
    """Retrieve authorization data through the MCP server.

    This private handler runs only after the Tool Gateway authorizes
    the request.
    """
    return call_local_mcp_tool_sync(
        tool_name="get_authorization",
        arguments={
            "authorization_id": authorization_id,
        },
    )


def get_authorization(
    authorization_id: str,
) -> dict[str, Any]:
    """Retrieve authorization information through the Tool Gateway.

    Args:
        authorization_id: Authorization identifier such as AUTH-9001.

    Returns:
        Authorization information returned by the MCP server with
        a gateway correlation ID.
    """
    context = get_tool_context(
        agent_name="authorization_agent",
    )

    gateway_response = execute_tool(
        tool_name="get_authorization",
        context=context,
        handler=_retrieve_authorization_from_mcp,
        arguments={
            "authorization_id": authorization_id,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    result = gateway_response["result"]

    return {
        **result,
        "correlation_id": gateway_response["correlation_id"],
    }