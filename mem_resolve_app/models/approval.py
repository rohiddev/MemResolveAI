from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ClaimAction(StrEnum):
    REVIEW_CODE_MISMATCH = "REVIEW_CODE_MISMATCH"
    CORRECT_AND_RESUBMIT = "CORRECT_AND_RESUBMIT"
    REQUEST_CLINICAL_REVIEW = "REQUEST_CLINICAL_REVIEW"


class ApprovalStatus(StrEnum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


class ApprovalDecision(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ApprovalRequest(BaseModel):
    request_id: str
    claim_id: str
    action: ClaimAction
    reason: str = Field(min_length=10)
    requested_by: str
    status: ApprovalStatus
    created_at: datetime

    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_comment: str | None = None

    executed_at: datetime | None = None