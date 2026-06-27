"""Business rules:
- Successful payment cannot exceed remaining unpaid amount.
- Fully paid invoice → paid status; partial → partially_paid.
- Failed payment should not increase amount_paid.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.plan import Plan
from app.repositories.customer_repo import CustomerRepository
from app.repositories.invoice_repo import InvoiceRepository
from app.repositories.plan_repo import PlanRepository


class TestPaymentBusinessRules:
    def _setup_invoice(self, db: Session, price: float = 100.00) -> tuple[int, int]:
        plan_repo = PlanRepository(db)
        plan = plan_repo.create(Plan(name="Pro", price=price, is_active=True))
        db.commit()

        cust_repo = CustomerRepository(db)
        customer = cust_repo.create(
            Customer(name="Test", email="paytest@example.com")
        )
        db.commit()

        return plan.id, customer.id

    def test_full_payment_marks_invoice_paid(self, client: TestClient, db: Session):
        plan_id, customer_id = self._setup_invoice(db, price=100.00)

        sub_resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan_id, "customer_id": customer_id},
        )
        sub_id = sub_resp.json()["id"]

        inv_resp = client.post("/api/v1/invoices", json={"subscription_id": sub_id})
        invoice_id = inv_resp.json()["id"]

        pay_resp = client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount": 100.00,
                "currency": "INR",
                "status": "success",
                "provider_reference": "txn_001",
            },
        )
        assert pay_resp.status_code == 201
        assert pay_resp.json()["invoice_status"] == "paid"

    def test_partial_payment_marks_invoice_partially_paid(
        self, client: TestClient, db: Session
    ):
        plan_id, customer_id = self._setup_invoice(db, price=100.00)

        sub_resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan_id, "customer_id": customer_id},
        )
        sub_id = sub_resp.json()["id"]

        inv_resp = client.post("/api/v1/invoices", json={"subscription_id": sub_id})
        invoice_id = inv_resp.json()["id"]

        pay_resp = client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount": 40.00,
                "currency": "INR",
                "status": "success",
                "provider_reference": "txn_002",
            },
        )
        assert pay_resp.status_code == 201
        assert pay_resp.json()["invoice_status"] == "partially_paid"

    def test_failed_payment_does_not_increase_amount_paid(
        self, client: TestClient, db: Session
    ):
        plan_id, customer_id = self._setup_invoice(db, price=100.00)

        sub_resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan_id, "customer_id": customer_id},
        )
        sub_id = sub_resp.json()["id"]

        inv_resp = client.post("/api/v1/invoices", json={"subscription_id": sub_id})
        invoice_id = inv_resp.json()["id"]

        client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount": 100.00,
                "currency": "INR",
                "status": "failed",
                "provider_reference": "txn_fail_001",
                "failure_reason": "Insufficient funds",
            },
        )

        inv_resp = client.get(f"/api/v1/invoices/{invoice_id}")
        assert float(inv_resp.json()["amount_paid"]) == 0.00

    def test_payment_exceeding_remaining_amount_rejected(
        self, client: TestClient, db: Session
    ):
        plan_id, customer_id = self._setup_invoice(db, price=100.00)

        sub_resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan_id, "customer_id": customer_id},
        )
        sub_id = sub_resp.json()["id"]

        inv_resp = client.post("/api/v1/invoices", json={"subscription_id": sub_id})
        invoice_id = inv_resp.json()["id"]

        pay_resp = client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount": 200.00,
                "currency": "INR",
                "status": "success",
                "provider_reference": "txn_003",
            },
        )
        assert pay_resp.status_code == 400
        assert "exceeds" in pay_resp.json()["detail"].lower()

    def test_ledger_entry_created_for_successful_payment(
        self, client: TestClient, db: Session
    ):
        plan_id, customer_id = self._setup_invoice(db, price=50.00)

        sub_resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan_id, "customer_id": customer_id},
        )
        sub_id = sub_resp.json()["id"]

        inv_resp = client.post("/api/v1/invoices", json={"subscription_id": sub_id})
        invoice_id = inv_resp.json()["id"]

        client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount": 50.00,
                "currency": "INR",
                "status": "success",
                "provider_reference": "txn_004",
            },
        )

        ledger_resp = client.get(f"/api/v1/ledger?customer_id={customer_id}")
        types = [e["entry_type"] for e in ledger_resp.json()]
        assert "payment_success" in types

    def test_ledger_entry_created_for_failed_payment(
        self, client: TestClient, db: Session
    ):
        plan_id, customer_id = self._setup_invoice(db, price=50.00)

        sub_resp = client.post(
            "/api/v1/subscriptions",
            json={"plan_id": plan_id, "customer_id": customer_id},
        )
        sub_id = sub_resp.json()["id"]

        inv_resp = client.post("/api/v1/invoices", json={"subscription_id": sub_id})
        invoice_id = inv_resp.json()["id"]

        client.post(
            "/api/v1/payments",
            json={
                "invoice_id": invoice_id,
                "amount": 50.00,
                "currency": "INR",
                "status": "failed",
                "provider_reference": "txn_fail_002",
                "failure_reason": "Card declined",
            },
        )

        ledger_resp = client.get(f"/api/v1/ledger?customer_id={customer_id}")
        types = [e["entry_type"] for e in ledger_resp.json()]
        assert "payment_failure" in types
