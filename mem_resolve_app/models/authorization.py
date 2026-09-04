from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class AuthorizationStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"


class Authorization(BaseModel):
    authorization_id: str
    member_id: str
    provider_id: str
    procedure_code: str
    diagnosis_code: str
    approved_from: date
    approved_through: date
    approved_units: int = Field(gt=0)
    status: AuthorizationStatus