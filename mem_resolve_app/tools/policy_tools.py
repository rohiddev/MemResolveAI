from typing import Any

from mem_resolve_app.knowledge.factory import get_policy_retriever
from mem_resolve_app.tool_gateway.context import get_tool_context
from mem_resolve_app.tool_gateway.gateway import execute_tool


def _search_policy_backend(
    query: str,
    maximum_results: int = 3,
) -> dict[str, Any]:
    """Search the configured knowledge backend.

    This private handler runs only after the Tool Gateway authorizes
    the request.
    """
    normalized_query = query.strip()

    if not normalized_query:
        return {
            "status": "INVALID_REQUEST",
            "query": query,
            "results": [],
            "message": "A policy search query is required.",
        }

    if maximum_results < 1 or maximum_results > 5:
        return {
            "status": "INVALID_REQUEST",
            "query": normalized_query,
            "results": [],
            "message": "maximum_results must be between 1 and 5.",
        }

    retriever = get_policy_retriever()

    matches = retriever.search(
        query=normalized_query,
        maximum_results=maximum_results,
    )

    if not matches:
        return {
            "status": "NO_MATCH",
            "query": normalized_query,
            "results": [],
            "message": "No relevant claim policy was found.",
        }

    return {
        "status": "FOUND",
        "query": normalized_query,
        "results": matches,
    }


def search_claim_policy(
    query: str,
    maximum_results: int = 3,
) -> dict[str, Any]:
    """Search approved claim policies through the Tool Gateway.

    Args:
        query: Policy question, denial code, or claim-resolution issue.
        maximum_results: Number of policy sections to retrieve.
            The allowed range is 1 through 5.

    Returns:
        Relevant policy sections with source metadata and a
        gateway correlation ID.
    """
    context = get_tool_context(
        agent_name="policy_agent",
    )

    gateway_response = execute_tool(
        tool_name="search_claim_policy",
        context=context,
        handler=_search_policy_backend,
        arguments={
            "query": query,
            "maximum_results": maximum_results,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    result = gateway_response["result"]

    return {
        **result,
        "correlation_id": gateway_response["correlation_id"],
    }