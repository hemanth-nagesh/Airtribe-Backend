"""Business rules:
- Cannot create subscription for an inactive plan.
- Customer cannot have two active subscriptions to the same plan.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.plan import Plan
from app.repositories.customer_repo import CustomerRepository
from app.repositories.plan_repo import PlanRepository


class TestSubscriptionBusinessRules:
    def _create_active_plan(self, db: Session) -> Plan:
        repo = PlanRepository(db)
        plan = repo.create(Plan(name="Pro", price=29.99, is_active=True))
        db.commit()
        return plan

    def _create_inactive_plan(self, db: Session) -> Plan:
        repo = PlanRepository(db)
        plan = repo.create(Plan(name="Retired", price=9.99, is_active=False))
        db.commit()
        return plan

    def _create_customer(self, db: Session) -> Customer:
        repo = CustomerRepository(db)
        customer = repo.create(Customer(name="Test", email="test@example.com"))
        db.commit()
        return customer

    def test_create_subscription_success(self, client: TestClient, db: Session):
        plan = self._create_active_plan(db)
        customer = self._create_customer(db)

        response = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan.id, "customer_id": customer.id},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "active"
        assert response.json()["plan_id"] == plan.id
        assert response.json()["customer_id"] == customer.id

    def test_create_subscription_inactive_plan_rejected(self, client: TestClient, db: Session):
        plan = self._create_inactive_plan(db)
        customer = self._create_customer(db)

        response = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan.id, "customer_id": customer.id},
        )
        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()

    def test_duplicate_active_subscription_rejected(self, client: TestClient, db: Session):
        plan = self._create_active_plan(db)
        customer = self._create_customer(db)

        # First subscription
        client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan.id, "customer_id": customer.id},
        )

        # Second subscription to same plan
        response = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan.id, "customer_id": customer.id},
        )
        assert response.status_code == 400
        assert "active subscription" in response.json()["detail"].lower()

    def test_create_subscription_plan_not_found(self, client: TestClient, db: Session):
        customer = self._create_customer(db)

        response = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": 9999, "customer_id": customer.id},
        )
        assert response.status_code == 404

    def test_cancel_subscription(self, client: TestClient, db: Session):
        plan = self._create_active_plan(db)
        customer = self._create_customer(db)

        resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan.id, "customer_id": customer.id},
        )
        sub_id = resp.json()["id"]

        response = client.post(f"/api/v1/subscriptions/{sub_id}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
