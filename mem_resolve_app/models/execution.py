from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class ExecutionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExecutionRecord(BaseModel):
    execution_id: str
    approval_request_id: str
    claim_id: str
    action: str
    executed_by: str
    status: ExecutionStatus
    result: str
    executed_at: datetime