from copy import copy
from typing import Any

import pytest

from mem_resolve_app.models.approval import ApprovalStatus
from mem_resolve_app.services import review_service


class FakeApprovalRequest:
    def __init__(
        self,
        *,
        request_id: str = "approval-test-001",
        claim_id: str = "CLM-20045",
        requested_by: str = "requester-01",
        status: ApprovalStatus = ApprovalStatus.PENDING_APPROVAL,
        reviewed_by: str | None = None,
        reviewed_at: Any = None,
        review_comment: str | None = None,
    ):
        self.request_id = request_id
        self.claim_id = claim_id
        self.requested_by = requested_by
        self.status = status
        self.reviewed_by = reviewed_by
        self.reviewed_at = reviewed_at
        self.review_comment = review_comment

    def model_copy(
        self,
        *,
        update: dict[str, Any],
    ) -> "FakeApprovalRequest":
        copied_request = copy(self)

        for field_name, field_value in update.items():
            setattr(copied_request, field_name, field_value)

        return copied_request

    def model_dump(
        self,
        *,
        mode: str,
    ) -> dict[str, Any]:
        del mode

        return {
            "request_id": self.request_id,
            "claim_id": self.claim_id,
            "requested_by": self.requested_by,
            "status": self.status.value,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": (
                self.reviewed_at.isoformat()
                if self.reviewed_at is not None
                else None
            ),
            "review_comment": self.review_comment,
        }


def test_requester_cannot_review_own_request(
    monkeypatch,
) -> None:
    approval_request = FakeApprovalRequest(
        requested_by="requester-01",
    )

    monkeypatch.setattr(
        review_service,
        "find_approval_request",
        lambda request_id: approval_request,
    )

    result = review_service.review_approval_request(
        request_id="approval-test-001",
        decision="APPROVE",
        reviewed_by="requester-01",
        review_comment="I approve this request.",
    )

    assert (
        result["status"]
        == "SEGREGATION_OF_DUTIES_VIOLATION"
    )
    assert (
        result["message"]
        == "The requester cannot review their own approval request."
    )


@pytest.mark.parametrize(
    "existing_status",
    [
        ApprovalStatus.APPROVED,
        ApprovalStatus.REJECTED,
    ],
)
def test_only_pending_request_can_be_reviewed(
    monkeypatch,
    existing_status: ApprovalStatus,
) -> None:
    approval_request = FakeApprovalRequest(
        status=existing_status,
    )

    monkeypatch.setattr(
        review_service,
        "find_approval_request",
        lambda request_id: approval_request,
    )

    result = review_service.review_approval_request(
        request_id="approval-test-001",
        decision="APPROVE",
        reviewed_by="reviewer-01",
        review_comment="Evidence supports this decision.",
    )

    assert result["status"] == "INVALID_STATE"
    assert result["current_status"] == existing_status.value
    assert (
        result["message"]
        == "Only a PENDING_APPROVAL request can be reviewed."
    )


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [
        ("APPROVE", ApprovalStatus.APPROVED),
        ("REJECT", ApprovalStatus.REJECTED),
    ],
)
def test_authorized_reviewer_can_record_decision(
    monkeypatch,
    decision: str,
    expected_status: ApprovalStatus,
) -> None:
    approval_request = FakeApprovalRequest()

    saved_requests: list[FakeApprovalRequest] = []

    def save_request(
        request: FakeApprovalRequest,
    ) -> FakeApprovalRequest:
        saved_requests.append(request)
        return request

    monkeypatch.setattr(
        review_service,
        "find_approval_request",
        lambda request_id: approval_request,
    )

    monkeypatch.setattr(
        review_service,
        "save_approval_request",
        save_request,
    )

    result = review_service.review_approval_request(
        request_id="approval-test-001",
        decision=decision,
        reviewed_by="reviewer-01",
        review_comment="Evidence supports this decision.",
    )

    assert result["status"] == "REVIEWED"
    assert result["decision"] == decision
    assert len(saved_requests) == 1

    saved_request = saved_requests[0]

    assert saved_request.status == expected_status
    assert saved_request.reviewed_by == "reviewer-01"
    assert (
        saved_request.review_comment
        == "Evidence supports this decision."
    )
    assert saved_request.reviewed_at is not None