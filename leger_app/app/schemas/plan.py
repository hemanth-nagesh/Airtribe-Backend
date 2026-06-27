from datetime import datetime

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    price: float = Field(..., gt=0)
    currency: str = "INR"
    billing_cycle: str = "monthly"
    is_active: bool = True


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(None, gt=0)
    currency: str | None = None
    billing_cycle: str | None = None
    is_active: bool | None = None


class PlanResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    currency: str
    billing_cycle: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
