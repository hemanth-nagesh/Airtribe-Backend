"""Business rule: Customer email must be unique."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.repositories.customer_repo import CustomerRepository


class TestCustomerBusinessRules:
    def test_create_customer_success(self, client: TestClient):
        response = client.post(
            "/api/v1/customers",
            json={"name": "Alice", "email": "alice@example.com"},
        )
        assert response.status_code == 201
        assert response.json()["email"] == "alice@example.com"

    def test_create_customer_duplicate_email_rejected(self, client: TestClient, db: Session):
        repo = CustomerRepository(db)
        repo.create(Customer(name="Alice", email="alice@example.com"))
        db.commit()

        response = client.post(
            "/api/v1/customers",
            json={"name": "Alice Again", "email": "alice@example.com"},
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_invalid_email_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/customers",
            json={"name": "Bob", "email": "not-an-email"},
        )
        assert response.status_code == 422

    def test_get_customer_by_id(self, client: TestClient, db: Session):
        repo = CustomerRepository(db)
        customer = repo.create(Customer(name="Charlie", email="charlie@example.com"))
        db.commit()

        response = client.get(f"/api/v1/customers/{customer.id}")
        assert response.status_code == 200
        assert response.json()["email"] == "charlie@example.com"

    def test_get_customer_not_found(self, client: TestClient):
        response = client.get("/api/v1/customers/9999")
        assert response.status_code == 404
