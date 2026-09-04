from datetime import UTC, datetime
from typing import Any

from mem_resolve_app.models.approval import (
    ApprovalDecision,
    ApprovalStatus,
)
from mem_resolve_app.repositories.approval_repository import (
    find_approval_request,
    save_approval_request,
)


def review_approval_request(
    *,
    request_id: str,
    decision: str,
    reviewed_by: str,
    review_comment: str,
) -> dict[str, Any]:
    """Approve or reject a pending approval request.

    This function enforces reviewer identity, segregation of duties,
    valid state transitions, and review-comment requirements.
    """
    normalized_request_id = request_id.strip()
    normalized_decision = decision.strip().upper()
    normalized_reviewer = reviewed_by.strip()
    normalized_comment = review_comment.strip()

    if not normalized_request_id:
        return {
            "status": "INVALID_REQUEST",
            "message": "request_id is required.",
        }

    if not normalized_reviewer:
        return {
            "status": "INVALID_REQUEST",
            "message": "reviewed_by is required.",
        }

    if len(normalized_comment) < 10:
        return {
            "status": "INVALID_REQUEST",
            "message": (
                "review_comment must contain at least 10 characters."
            ),
        }

    try:
        approval_decision = ApprovalDecision(normalized_decision)
    except ValueError:
        return {
            "status": "INVALID_DECISION",
            "decision": normalized_decision,
            "allowed_decisions": [
                allowed_decision.value
                for allowed_decision in ApprovalDecision
            ],
            "message": (
                f"Decision {normalized_decision} is not allowed."
            ),
        }

    approval_request = find_approval_request(
        normalized_request_id
    )

    if approval_request is None:
        return {
            "status": "NOT_FOUND",
            "request_id": normalized_request_id,
            "message": (
                f"Approval request {normalized_request_id} was not found."
            ),
        }

    if approval_request.requested_by == normalized_reviewer:
        return {
            "status": "SEGREGATION_OF_DUTIES_VIOLATION",
            "request_id": normalized_request_id,
            "message": (
                "The requester cannot review their own approval request."
            ),
        }

    if approval_request.status != ApprovalStatus.PENDING_APPROVAL:
        return {
            "status": "INVALID_STATE",
            "request_id": normalized_request_id,
            "current_status": approval_request.status.value,
            "message": (
                "Only a PENDING_APPROVAL request can be reviewed."
            ),
        }

    if approval_decision == ApprovalDecision.APPROVE:
        new_status = ApprovalStatus.APPROVED
    else:
        new_status = ApprovalStatus.REJECTED

    reviewed_request = approval_request.model_copy(
        update={
            "status": new_status,
            "reviewed_by": normalized_reviewer,
            "reviewed_at": datetime.now(UTC),
            "review_comment": normalized_comment,
        }
    )

    saved_request = save_approval_request(reviewed_request)

    return {
        "status": "REVIEWED",
        "decision": approval_decision.value,
        "approval_request": saved_request.model_dump(mode="json"),
        "message": (
            f"Approval request was {new_status.value.lower()}."
        ),
    }