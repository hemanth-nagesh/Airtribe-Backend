from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.models.subscription import Subscription
from app.repositories.plan_repo import PlanRepository
from app.repositories.subscription_repo import SubscriptionRepository
from app.schemas.subscription import SubscriptionCreate


class SubscriptionService:
    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        plan_repo: PlanRepository,
    ):
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo

    def create_subscription(self, data: SubscriptionCreate) -> Subscription:
        plan = self.plan_repo.get_by_id(data.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if not plan.is_active:
            raise HTTPException(status_code=400, detail="Cannot subscribe to an inactive plan")

        existing = self.subscription_repo.get_active_by_customer_and_plan(
            data.customer_id, data.plan_id
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Customer already has an active subscription to this plan",
            )

        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=30)

        subscription = Subscription(
            plan_id=data.plan_id,
            customer_id=data.customer_id,
            status="active",
            current_period_start=now,
            current_period_end=period_end,
        )
        return self.subscription_repo.create(subscription)

    def get_subscription(self, subscription_id: int) -> Subscription | None:
        return self.subscription_repo.get_by_id(subscription_id)

    def list_subscriptions(
        self, customer_id: int | None = None, plan_id: int | None = None
    ) -> list[Subscription]:
        return self.subscription_repo.get_all(
            customer_id=customer_id, plan_id=plan_id
        )

    def cancel_subscription(self, subscription: Subscription) -> Subscription:
        subscription.status = "cancelled"
        return self.subscription_repo.update(subscription)
