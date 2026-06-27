from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.invoice_repo import InvoiceRepository
from app.repositories.ledger_repo import LedgerRepository
from app.repositories.payment_attempt_repo import PaymentAttemptRepository
from app.schemas.payment_attempt import PaymentRecord, PaymentResponse
from app.services.ledger_service import LedgerService
from app.services.payment_service import PaymentService

router = APIRouter(tags=["Payments"])


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(
        InvoiceRepository(db),
        PaymentAttemptRepository(db),
        LedgerService(LedgerRepository(db)),
    )


@router.post("/payments", response_model=PaymentResponse, status_code=201)
def record_payment(
    data: PaymentRecord,
    service: PaymentService = Depends(get_payment_service),
):
    attempt, invoice_status = service.record_payment(data)
    return PaymentResponse(
        id=attempt.id,
        invoice_id=attempt.invoice_id,
        amount=float(attempt.amount),
        currency=attempt.currency,
        status=attempt.status,
        provider_reference=attempt.provider_reference,
        failure_reason=attempt.failure_reason,
        created_at=attempt.created_at,
        invoice_status=invoice_status,
    )
