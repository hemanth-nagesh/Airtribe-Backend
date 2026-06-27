from datetime import datetime

from pydantic import BaseModel, Field


class InvoiceGenerate(BaseModel):
    subscription_id: int


class InvoiceStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(issued|paid|partially_paid|void)$")


class InvoiceResponse(BaseModel):
    id: int
    subscription_id: int
    customer_id: int | None
    amount_due: float
    amount_paid: float
    currency: str
    status: str
    period_start: datetime | None
    period_end: datetime | None
    due_date: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
