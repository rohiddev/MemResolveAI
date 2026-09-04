from datetime import date
from enum import StrEnum

from pydantic import BaseModel


class CoverageStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class EligibilityRecord(BaseModel):
    member_id: str
    plan_name: str
    plan_type: str
    group_number: str
    effective_date: date
    termination_date: date | None = None
    status: CoverageStatus