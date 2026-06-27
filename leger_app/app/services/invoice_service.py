from datetime import datetime, timezone

from fastapi import HTTPException

from app.models.invoice import Invoice
from app.repositories.invoice_repo import InvoiceRepository
from app.repositories.plan_repo import PlanRepository
from app.repositories.subscription_repo import SubscriptionRepository
from app.services.ledger_service import LedgerService


class InvoiceService:
    def __init__(
        self,
        subscription_repo: SubscriptionRepository,
        plan_repo: PlanRepository,
        invoice_repo: InvoiceRepository,
        ledger_service: LedgerService,
    ):
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.invoice_repo = invoice_repo
        self.ledger_service = ledger_service

    def generate_invoice(self, subscription_id: int) -> Invoice:
        subscription = self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        if subscription.status != "active":
            raise HTTPException(
                status_code=400, detail="Cannot generate invoice for a non-active subscription"
            )

        plan = self.plan_repo.get_by_id(subscription.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        now = datetime.now(timezone.utc)
        invoice = Invoice(
            subscription_id=subscription.id,
            customer_id=subscription.customer_id,
            amount_due=float(plan.price),
            amount_paid=0.00,
            currency=plan.currency,
            status="issued",
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            due_date=now,
        )
        invoice = self.invoice_repo.create(invoice)

        self.ledger_service.create_entry(
            entry_type="invoice_created",
            invoice_id=invoice.id,
            customer_id=subscription.customer_id,
            amount=float(plan.price),
            currency=plan.currency,
            reference_id=f"inv-{invoice.id}",
            description=f"Invoice #{invoice.id} generated for subscription #{subscription.id}",
        )

        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice | None:
        return self.invoice_repo.get_by_id(invoice_id)

    def list_invoices(
        self, subscription_id: int | None = None, customer_id: int | None = None
    ) -> list[Invoice]:
        return self.invoice_repo.get_all(
            subscription_id=subscription_id, customer_id=customer_id
        )
