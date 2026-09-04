import asyncio
from datetime import date
from typing import Any

from mcp.server import MCPServer

from mem_resolve_app.repositories.authorization_repository import (
    find_authorization,
)
from mem_resolve_app.repositories.claim_repository import find_claim
from mem_resolve_app.repositories.eligibility_repository import (
    find_eligibility,
    is_covered_on_date,
)
from mem_resolve_app.services.approval_service import (
    create_pending_approval,
    retrieve_approval,
)
from mem_resolve_app.services.execution_service import (
    execute_approved_action as execute_approved_action_service,
    retrieve_execution,
)
from mem_resolve_app.services.review_service import (
    review_approval_request,
)


mcp = MCPServer("memresolve-operational-tools")


def _get_claim_record(
    claim_id: str,
) -> dict[str, Any]:
    """Retrieve a claim from Firestore."""
    normalized_claim_id = claim_id.strip().upper()

    if not normalized_claim_id:
        return {
            "status": "INVALID_REQUEST",
            "message": "claim_id is required.",
        }

    claim = find_claim(normalized_claim_id)

    if claim is None:
        return {
            "status": "NOT_FOUND",
            "claim_id": normalized_claim_id,
            "message": f"Claim {normalized_claim_id} was not found.",
        }

    return {
        "status": "FOUND",
        "claim": claim.model_dump(mode="json"),
    }


@mcp.tool()
async def get_claim(
    claim_id: str,
) -> dict[str, Any]:
    """Retrieve a healthcare claim.

    Args:
        claim_id: Claim identifier such as CLM-20045.

    Returns:
        Structured claim information or a not-found response.
    """
    return await asyncio.to_thread(
        _get_claim_record,
        claim_id,
    )


def _get_authorization_record(
    authorization_id: str,
) -> dict[str, Any]:
    """Retrieve a prior authorization from Firestore."""
    normalized_id = authorization_id.strip().upper()

    if not normalized_id:
        return {
            "status": "INVALID_REQUEST",
            "message": "authorization_id is required.",
        }

    authorization = find_authorization(normalized_id)

    if authorization is None:
        return {
            "status": "NOT_FOUND",
            "authorization_id": normalized_id,
            "message": f"Authorization {normalized_id} was not found.",
        }

    return {
        "status": "FOUND",
        "authorization": authorization.model_dump(mode="json"),
    }


@mcp.tool()
async def get_authorization(
    authorization_id: str,
) -> dict[str, Any]:
    """Retrieve a prior authorization.

    Args:
        authorization_id: Authorization identifier such as AUTH-9001.

    Returns:
        Structured authorization information or a not-found response.
    """
    return await asyncio.to_thread(
        _get_authorization_record,
        authorization_id,
    )


def _check_eligibility_record(
    member_id: str,
    service_date: str,
) -> dict[str, Any]:
    """Check eligibility using deterministic business rules."""
    normalized_member_id = member_id.strip().upper()

    if not normalized_member_id:
        return {
            "status": "INVALID_REQUEST",
            "message": "member_id is required.",
        }

    try:
        parsed_service_date = date.fromisoformat(service_date)
    except ValueError:
        return {
            "status": "INVALID_REQUEST",
            "member_id": normalized_member_id,
            "service_date": service_date,
            "message": "Service date must use YYYY-MM-DD format.",
        }

    eligibility = find_eligibility(normalized_member_id)

    if eligibility is None:
        return {
            "status": "NOT_FOUND",
            "member_id": normalized_member_id,
            "service_date": service_date,
            "message": (
                f"Eligibility information for {normalized_member_id} "
                "was not found."
            ),
        }

    covered = is_covered_on_date(
        record=eligibility,
        service_date=parsed_service_date,
    )

    return {
        "status": "FOUND",
        "member_id": normalized_member_id,
        "service_date": service_date,
        "covered_on_service_date": covered,
        "eligibility": eligibility.model_dump(mode="json"),
    }


@mcp.tool()
async def check_eligibility(
    member_id: str,
    service_date: str,
) -> dict[str, Any]:
    """Check member coverage on a service date.

    Args:
        member_id: Member identifier such as MBR-1001.
        service_date: Service date in YYYY-MM-DD format.

    Returns:
        Eligibility information and the coverage determination.
    """
    return await asyncio.to_thread(
        _check_eligibility_record,
        member_id,
        service_date,
    )


@mcp.tool()
async def create_approval_request(
    claim_id: str,
    action: str,
    reason: str,
    requested_by: str,
) -> dict[str, Any]:
    """Create a persistent human approval request.

    Args:
        claim_id: Claim identifier such as CLM-20045.
        action: REVIEW_CODE_MISMATCH, CORRECT_AND_RESUBMIT, or
            REQUEST_CLINICAL_REVIEW.
        reason: Evidence-based reason for the requested action.
        requested_by: Identity of the requesting user.

    Returns:
        A PENDING_APPROVAL request, an existing pending request,
        or a validation response.
    """
    return await asyncio.to_thread(
        create_pending_approval,
        claim_id=claim_id,
        action=action,
        reason=reason,
        requested_by=requested_by,
    )


@mcp.tool()
async def get_approval_request(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve a persistent approval request.

    Args:
        request_id: Unique approval request identifier.

    Returns:
        Approval request information or a not-found response.
    """
    return await asyncio.to_thread(
        retrieve_approval,
        request_id=request_id,
    )


@mcp.tool()
async def approve_request(
    request_id: str,
    reviewed_by: str,
    review_comment: str,
) -> dict[str, Any]:
    """Approve a pending claim-action request.

    Args:
        request_id: Unique approval request identifier.
        reviewed_by: Identity of the human reviewer.
        review_comment: Evidence-based approval explanation.

    Returns:
        Reviewed approval information or a controlled error.
    """
    return await asyncio.to_thread(
        review_approval_request,
        request_id=request_id,
        decision="APPROVE",
        reviewed_by=reviewed_by,
        review_comment=review_comment,
    )


@mcp.tool()
async def reject_request(
    request_id: str,
    reviewed_by: str,
    review_comment: str,
) -> dict[str, Any]:
    """Reject a pending claim-action request.

    Args:
        request_id: Unique approval request identifier.
        reviewed_by: Identity of the human reviewer.
        review_comment: Evidence-based rejection explanation.

    Returns:
        Reviewed approval information or a controlled error.
    """
    return await asyncio.to_thread(
        review_approval_request,
        request_id=request_id,
        decision="REJECT",
        reviewed_by=reviewed_by,
        review_comment=review_comment,
    )


@mcp.tool()
async def execute_approved_action(
    request_id: str,
    executed_by: str,
) -> dict[str, Any]:
    """Execute an approved claim-resolution action exactly once.

    Args:
        request_id: Approved request identifier.
        executed_by: Identity of the authorized executor.

    Returns:
        Execution information or a controlled validation response.
    """
    return await asyncio.to_thread(
        execute_approved_action_service,
        request_id=request_id,
        executed_by=executed_by,
    )


@mcp.tool()
async def get_execution(
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an execution record.

    Args:
        request_id: Approval request identifier.

    Returns:
        Execution information or a not-found response.
    """
    return await asyncio.to_thread(
        retrieve_execution,
        request_id=request_id,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")