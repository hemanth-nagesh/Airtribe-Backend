"""Business rule: Plan price must be greater than 0."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.repositories.plan_repo import PlanRepository


class TestPlanBusinessRules:
    def test_create_plan_success(self, client: TestClient):
        response = client.post(
            "/api/v1/plans",
            json={"name": "Basic", "price": 10.99, "currency": "INR"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Basic"
        assert float(data["price"]) == 10.99
        assert data["is_active"] is True

    def test_create_plan_zero_price_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/plans",
            json={"name": "Free", "price": 0},
        )
        assert response.status_code == 422  # Pydantic validation catches gt=0

    def test_create_plan_negative_price_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/plans",
            json={"name": "Negative", "price": -50},
        )
        assert response.status_code == 422

    def test_list_plans_default_active_only(self, client: TestClient, db: Session):
        repo = PlanRepository(db)
        active = Plan(name="Active", price=10, is_active=True)
        inactive = Plan(name="Inactive", price=20, is_active=False)
        repo.create(active)
        repo.create(inactive)
        db.commit()

        response = client.get("/api/v1/plans")
        assert response.status_code == 200
        plans = response.json()
        names = [p["name"] for p in plans]
        assert "Active" in names
        assert "Inactive" not in names

    def test_list_plans_include_inactive(self, client: TestClient, db: Session):
        repo = PlanRepository(db)
        repo.create(Plan(name="Active", price=10, is_active=True))
        repo.create(Plan(name="Inactive", price=20, is_active=False))
        db.commit()

        response = client.get("/api/v1/plans?include_inactive=true")
        assert response.status_code == 200
        assert len(response.json()) == 2
