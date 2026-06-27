from datetime import datetime

from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    plan_id: int
    customer_id: int


class SubscriptionCancel(BaseModel):
    pass


class SubscriptionResponse(BaseModel):
    id: int
    plan_id: int
    customer_id: int
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
