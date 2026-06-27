"""Business rule: Invoice amount_due should come from the plan price at the time invoice is generated."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.plan import Plan
from app.repositories.customer_repo import CustomerRepository
from app.repositories.plan_repo import PlanRepository


class TestInvoiceBusinessRules:
    def _setup(self, db: Session, price: float = 49.99) -> tuple[int, int]:
        plan_repo = PlanRepository(db)
        plan = plan_repo.create(Plan(name="Premium", price=price, is_active=True))
        db.commit()

        cust_repo = CustomerRepository(db)
        customer = cust_repo.create(
            Customer(name="Test", email="test@example.com")
        )
        db.commit()
        return plan.id, customer.id

    def test_generate_invoice_uses_plan_price(self, client: TestClient, db: Session):
        plan_id, customer_id = self._setup(db, price=49.99)

        sub_resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan_id, "customer_id": customer_id},
        )
        sub_id = sub_resp.json()["id"]

        inv_resp = client.post(
            "/api/v1/invoices",
            json={"subscription_id": sub_id},
        )
        assert inv_resp.status_code == 201
        assert float(inv_resp.json()["amount_due"]) == 49.99
        assert inv_resp.json()["status"] == "issued"

    def test_generate_invoice_for_inactive_subscription_rejected(
        self, client: TestClient, db: Session
    ):
        plan_id, customer_id = self._setup(db)

        sub_resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan_id, "customer_id": customer_id},
        )
        sub_id = sub_resp.json()["id"]

        # Cancel the subscription first
        client.post(f"/api/v1/subscriptions/{sub_id}/cancel")

        inv_resp = client.post(
            "/api/v1/invoices",
            json={"subscription_id": sub_id},
        )
        assert inv_resp.status_code == 400
        assert "non-active" in inv_resp.json()["detail"].lower()

    def test_generate_invoice_creates_ledger_entry(
        self, client: TestClient, db: Session
    ):
        plan_id, customer_id = self._setup(db)

        sub_resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan_id, "customer_id": customer_id},
        )
        sub_id = sub_resp.json()["id"]

        client.post("/api/v1/invoices", json={"subscription_id": sub_id})

        ledger_resp = client.get(
            f"/api/v1/ledger?customer_id={customer_id}"
        )
        assert ledger_resp.status_code == 200
        types = [e["entry_type"] for e in ledger_resp.json()]
        assert "invoice_created" in types
