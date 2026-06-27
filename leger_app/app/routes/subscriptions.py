from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.plan_repo import PlanRepository
from app.repositories.subscription_repo import SubscriptionRepository
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(tags=["Subscriptions"])


def get_subscription_service(db: Session = Depends(get_db)) -> SubscriptionService:
    return SubscriptionService(
        SubscriptionRepository(db),
        PlanRepository(db),
    )


@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=201)
def create_subscription(
    data: SubscriptionCreate,
    service: SubscriptionService = Depends(get_subscription_service),
):
    return service.create_subscription(data)


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
def list_subscriptions(
    customer_id: int | None = None,
    plan_id: int | None = None,
    service: SubscriptionService = Depends(get_subscription_service),
):
    return service.list_subscriptions(customer_id=customer_id, plan_id=plan_id)


@router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: int,
    service: SubscriptionService = Depends(get_subscription_service),
):
    sub = service.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.post(
    "/subscriptions/{subscription_id}/cancel",
    response_model=SubscriptionResponse,
)
def cancel_subscription(
    subscription_id: int,
    service: SubscriptionService = Depends(get_subscription_service),
):
    sub = service.get_subscription(subscription_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if sub.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Only active subscriptions can be cancelled",
        )
    return service.cancel_subscription(sub)
