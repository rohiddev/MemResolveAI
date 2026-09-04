from typing import Any

from mem_resolve_app.repositories.claim_repository import find_claim
from mem_resolve_app.tool_gateway.context import get_tool_context
from mem_resolve_app.tool_gateway.gateway import execute_tool


def _retrieve_claim(claim_id: str) -> dict[str, Any]:
    """Retrieve a claim from the repository.

    This private handler is called only after the Tool Gateway
    authorizes the request.
    """
    claim = find_claim(claim_id)

    if claim is None:
        return {
            "status": "NOT_FOUND",
            "claim_id": claim_id.strip().upper(),
            "message": f"Claim {claim_id} was not found.",
        }

    return {
        "status": "FOUND",
        "claim": claim.model_dump(mode="json"),
    }


def get_claim(claim_id: str) -> dict[str, Any]:
    """Retrieve claim information through the governed Tool Gateway.

    Args:
        claim_id: Claim identifier such as CLM-20045.

    Returns:
        The claim result with a correlation ID, or a controlled
        gateway error.
    """
    context = get_tool_context(agent_name="claim_agent")

    gateway_response = execute_tool(
        tool_name="get_claim",
        context=context,
        handler=_retrieve_claim,
        arguments={
            "claim_id": claim_id,
        },
    )

    if gateway_response["status"] != "SUCCEEDED":
        return gateway_response

    result = gateway_response["result"]

    return {
        **result,
        "correlation_id": gateway_response["correlation_id"],
    }