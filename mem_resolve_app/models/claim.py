from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class ClaimStatus(StrEnum):
    RECEIVED = "RECEIVED"
    PENDING = "PENDING"
    PAID = "PAID"
    DENIED = "DENIED"


class Claim(BaseModel):
    claim_id: str
    member_id: str
    provider_id: str
    service_date: date
    procedure_code: str
    diagnosis_code: str
    billed_amount: Decimal = Field(ge=0)
    allowed_amount: Decimal = Field(ge=0)
    status: ClaimStatus
    denial_code: str | None = None
    denial_reason: str | None = None
    authorization_id: str | None = None