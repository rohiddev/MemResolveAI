from datetime import UTC, datetime

import pytest

from mem_resolve_app.models.approval import (
    ApprovalRequest,
    ApprovalStatus,
    ClaimAction,
)
from mem_resolve_app.services import approval_service


@pytest.mark.parametrize(
    ("arguments", "expected_message"),
    [
        (
            {
                "claim_id": " ",
                "action": "REVIEW_CODE_MISMATCH",
                "reason": "Procedure codes do not match.",
                "requested_by": "requester-01",
            },
            "claim_id is required.",
        ),
        (
            {
                "claim_id": "CLM-20045",
                "action": "REVIEW_CODE_MISMATCH",
                "reason": "Procedure codes do not match.",
                "requested_by": " ",
            },
            "requested_by is required.",
        ),
        (
            {
                "claim_id": "CLM-20045",
                "action": "REVIEW_CODE_MISMATCH",
                "reason": "Too short",
                "requested_by": "requester-01",
            },
            "Reason must contain at least 10 characters.",
        ),
    ],
)
def test_required_approval_fields_are_enforced(
    arguments: dict[str, str],
    expected_message: str,
) -> None:
    result = approval_service.create_pending_approval(
        **arguments,
    )

    assert result["status"] == "INVALID_REQUEST"
    assert result["message"] == expected_message


def test_only_allowed_claim_actions_are_accepted() -> None:
    result = approval_service.create_pending_approval(
        claim_id="CLM-20045",
        action="AUTOMATICALLY_PAY_CLAIM",
        reason="Attempt an action outside the approved catalog.",
        requested_by="requester-01",
    )

    assert result["status"] == "INVALID_ACTION"
    assert result["action"] == "AUTOMATICALLY_PAY_CLAIM"
    assert result["allowed_actions"] == [
        "REVIEW_CODE_MISMATCH",
        "CORRECT_AND_RESUBMIT",
        "REQUEST_CLINICAL_REVIEW",
    ]


def test_duplicate_pending_request_is_not_created(
    monkeypatch,
) -> None:
    existing_request = ApprovalRequest(
        request_id="approval-existing-001",
        claim_id="CLM-20045",
        action=ClaimAction.REVIEW_CODE_MISMATCH,
        reason="Claim and authorization procedure codes differ.",
        requested_by="requester-01",
        status=ApprovalStatus.PENDING_APPROVAL,
        created_at=datetime.now(UTC),
    )

    monkeypatch.setattr(
        approval_service,
        "find_pending_request",
        lambda *, claim_id, action: existing_request,
    )

    def unexpected_save(
        request: ApprovalRequest,
    ) -> ApprovalRequest:
        raise AssertionError(
            "A duplicate approval request must not be saved."
        )

    monkeypatch.setattr(
        approval_service,
        "save_approval_request",
        unexpected_save,
    )

    result = approval_service.create_pending_approval(
        claim_id="clm-20045",
        action="review_code_mismatch",
        reason="Claim and authorization procedure codes differ.",
        requested_by="requester-02",
    )

    assert result["status"] == "EXISTING_PENDING_REQUEST"
    assert (
        result["approval_request"]["request_id"]
        == "approval-existing-001"
    )


def test_valid_request_is_created_as_pending(
    monkeypatch,
) -> None:
    saved_requests: list[ApprovalRequest] = []

    monkeypatch.setattr(
        approval_service,
        "find_pending_request",
        lambda *, claim_id, action: None,
    )

    monkeypatch.setattr(
        approval_service,
        "uuid4",
        lambda: "approval-new-001",
    )

    def save_request(
        request: ApprovalRequest,
    ) -> ApprovalRequest:
        saved_requests.append(request)
        return request

    monkeypatch.setattr(
        approval_service,
        "save_approval_request",
        save_request,
    )

    result = approval_service.create_pending_approval(
        claim_id=" clm-20045 ",
        action=" review_code_mismatch ",
        reason=" Claim and authorization codes do not match. ",
        requested_by=" requester-01 ",
    )

    assert result["status"] == "CREATED"
    assert len(saved_requests) == 1

    saved_request = saved_requests[0]

    assert saved_request.request_id == "approval-new-001"
    assert saved_request.claim_id == "CLM-20045"
    assert (
        saved_request.action
        == ClaimAction.REVIEW_CODE_MISMATCH
    )
    assert saved_request.requested_by == "requester-01"
    assert (
        saved_request.status
        == ApprovalStatus.PENDING_APPROVAL
    )
    assert saved_request.reviewed_by is None
    assert saved_request.executed_at is None
    assert saved_request.created_at.tzinfo is not None


def test_retrieve_unknown_approval_returns_not_found(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        approval_service,
        "find_approval_request",
        lambda request_id: None,
    )

    result = approval_service.retrieve_approval(
        request_id="approval-missing-001",
    )

    assert result == {
        "status": "NOT_FOUND",
        "request_id": "approval-missing-001",
        "message": (
            "Approval request approval-missing-001 was not found."
        ),
    }