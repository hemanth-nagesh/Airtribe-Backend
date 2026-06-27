from datetime import datetime

from pydantic import BaseModel, Field


class PaymentRecord(BaseModel):
    invoice_id: int
    amount: float = Field(..., gt=0)
    currency: str = "INR"
    status: str = Field(..., pattern=r"^(success|failed)$")
    provider_reference: str | None = None
    failure_reason: str | None = None


class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: float
    currency: str
    status: str
    provider_reference: str | None
    failure_reason: str | None
    created_at: datetime
    invoice_status: str | None = None

    model_config = {"from_attributes": True}
