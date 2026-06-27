from sqlalchemy.orm import Session

from app.models.subscription import Subscription


class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, subscription: Subscription) -> Subscription:
        self.db.add(subscription)
        self.db.flush()
        return subscription

    def get_by_id(self, subscription_id: int) -> Subscription | None:
        return (
            self.db.query(Subscription)
            .filter(Subscription.id == subscription_id)
            .first()
        )

    def get_all(
        self, customer_id: int | None = None, plan_id: int | None = None
    ) -> list[Subscription]:
        query = self.db.query(Subscription)
        if customer_id is not None:
            query = query.filter(Subscription.customer_id == customer_id)
        if plan_id is not None:
            query = query.filter(Subscription.plan_id == plan_id)
        return query.all()

    def get_active_by_customer_and_plan(
        self, customer_id: int, plan_id: int
    ) -> Subscription | None:
        return (
            self.db.query(Subscription)
            .filter(
                Subscription.customer_id == customer_id,
                Subscription.plan_id == plan_id,
                Subscription.status == "active",
            )
            .first()
        )

    def update(self, subscription: Subscription) -> Subscription:
        self.db.flush()
        return subscription
