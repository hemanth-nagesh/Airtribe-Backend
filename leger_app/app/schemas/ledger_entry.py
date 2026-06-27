from datetime import datetime

from pydantic import BaseModel


class LedgerEntryResponse(BaseModel):
    id: int
    invoice_id: int | None
    subscription_id: int | None
    customer_id: int
    entry_type: str
    amount: float
    currency: str
    description: str | None
    reference_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
