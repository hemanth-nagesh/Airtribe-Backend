from fastapi import HTTPException

from app.models.payment_attempt import PaymentAttempt
from app.repositories.invoice_repo import InvoiceRepository
from app.repositories.payment_attempt_repo import PaymentAttemptRepository
from app.schemas.payment_attempt import PaymentRecord
from app.services.ledger_service import LedgerService


class PaymentService:
    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        payment_attempt_repo: PaymentAttemptRepository,
        ledger_service: LedgerService,
    ):
        self.invoice_repo = invoice_repo
        self.payment_attempt_repo = payment_attempt_repo
        self.ledger_service = ledger_service

    def record_payment(self, data: PaymentRecord) -> tuple[PaymentAttempt, str]:
        invoice = self.invoice_repo.get_by_id(data.invoice_id)
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        payment_attempt = PaymentAttempt(
            invoice_id=data.invoice_id,
            amount=data.amount,
            currency=data.currency,
            status=data.status,
            provider_reference=data.provider_reference,
            failure_reason=data.failure_reason,
        )
        payment_attempt = self.payment_attempt_repo.create(payment_attempt)

        if data.status == "failed":
            self.ledger_service.create_entry(
                entry_type="payment_failure",
                invoice_id=data.invoice_id,
                customer_id=invoice.customer_id,
                amount=data.amount,
                currency=data.currency,
                reference_id=data.provider_reference or f"pmt-{payment_attempt.id}",
                description=data.failure_reason or "Payment failed",
            )
            return payment_attempt, invoice.status

        remaining = float(invoice.amount_due) - float(invoice.amount_paid)
        if data.amount > remaining:
            raise HTTPException(
                status_code=400,
                detail=f"Payment amount {data.amount} exceeds remaining unpaid amount {remaining}",
            )

        new_amount_paid = float(invoice.amount_paid) + data.amount
        invoice.amount_paid = new_amount_paid

        if new_amount_paid >= float(invoice.amount_due):
            invoice.status = "paid"
        else:
            invoice.status = "partially_paid"

        self.invoice_repo.update(invoice)

        self.ledger_service.create_entry(
            entry_type="payment_success",
            invoice_id=data.invoice_id,
            customer_id=invoice.customer_id,
            amount=data.amount,
            currency=data.currency,
            reference_id=data.provider_reference or f"pmt-{payment_attempt.id}",
            description=f"Payment of {data.amount} {data.currency} received for invoice #{data.invoice_id}",
        )

        return payment_attempt, invoice.status
