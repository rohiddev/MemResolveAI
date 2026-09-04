from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from mem_resolve_app.models.approval import (
    ApprovalRequest,
    ApprovalStatus,
    ClaimAction,
)
from mem_resolve_app.repositories.approval_repository import (
    find_approval_request,
    find_pending_request,
    save_approval_request,
)


def create_pending_approval(
    *,
    claim_id: str,
    action: str,
    reason: str,
    requested_by: str,
) -> dict[str, Any]:
    """Create a persistent pending approval request.

    This is deterministic business logic. It does not contain any
    LLM or MCP-specific code.
    """
    normalized_claim_id = claim_id.strip().upper()
    normalized_action = action.strip().upper()
    normalized_reason = reason.strip()
    normalized_requester = requested_by.strip()

    if not normalized_claim_id:
        return {
            "status": "INVALID_REQUEST",
            "message": "claim_id is required.",
        }

    if not normalized_requester:
        return {
            "status": "INVALID_REQUEST",
            "message": "requested_by is required.",
        }

    if len(normalized_reason) < 10:
        return {
            "status": "INVALID_REQUEST",
            "message": "Reason must contain at least 10 characters.",
        }

    try:
        claim_action = ClaimAction(normalized_action)
    except ValueError:
        return {
            "status": "INVALID_ACTION",
            "action": normalized_action,
            "allowed_actions": [
                allowed_action.value
                for allowed_action in ClaimAction
            ],
            "message": f"Action {normalized_action} is not allowed.",
        }

    existing_request = find_pending_request(
        claim_id=normalized_claim_id,
        action=claim_action,
    )

    if existing_request is not None:
        return {
            "status": "EXISTING_PENDING_REQUEST",
            "message": (
                "A pending approval request already exists for this "
                "claim and action."
            ),
            "approval_request": existing_request.model_dump(mode="json"),
        }

    approval_request = ApprovalRequest(
        request_id=str(uuid4()),
        claim_id=normalized_claim_id,
        action=claim_action,
        reason=normalized_reason,
        requested_by=normalized_requester,
        status=ApprovalStatus.PENDING_APPROVAL,
        created_at=datetime.now(UTC),
    )

    saved_request = save_approval_request(approval_request)

    return {
        "status": "CREATED",
        "message": "Approval request created successfully.",
        "approval_request": saved_request.model_dump(mode="json"),
    }


def retrieve_approval(
    *,
    request_id: str,
) -> dict[str, Any]:
    """Retrieve a persistent approval request."""
    normalized_request_id = request_id.strip()

    if not normalized_request_id:
        return {
            "status": "INVALID_REQUEST",
            "message": "request_id is required.",
        }

    approval_request = find_approval_request(normalized_request_id)

    if approval_request is None:
        return {
            "status": "NOT_FOUND",
            "request_id": normalized_request_id,
            "message": (
                f"Approval request {normalized_request_id} was not found."
            ),
        }

    return {
        "status": "FOUND",
        "approval_request": approval_request.model_dump(mode="json"),
    }