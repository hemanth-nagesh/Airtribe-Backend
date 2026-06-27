from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.invoice_repo import InvoiceRepository
from app.repositories.ledger_repo import LedgerRepository
from app.repositories.plan_repo import PlanRepository
from app.repositories.subscription_repo import SubscriptionRepository
from app.schemas.invoice import InvoiceGenerate, InvoiceResponse
from app.services.invoice_service import InvoiceService
from app.services.ledger_service import LedgerService

router = APIRouter(tags=["Invoices"])


def get_invoice_service(db: Session = Depends(get_db)) -> InvoiceService:
    return InvoiceService(
        SubscriptionRepository(db),
        PlanRepository(db),
        InvoiceRepository(db),
        LedgerService(LedgerRepository(db)),
    )


@router.post("/invoices", response_model=InvoiceResponse, status_code=201)
def generate_invoice(
    data: InvoiceGenerate,
    service: InvoiceService = Depends(get_invoice_service),
):
    return service.generate_invoice(data.subscription_id)


@router.get("/invoices", response_model=list[InvoiceResponse])
def list_invoices(
    subscription_id: int | None = None,
    customer_id: int | None = None,
    service: InvoiceService = Depends(get_invoice_service),
):
    return service.list_invoices(
        subscription_id=subscription_id, customer_id=customer_id
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    service: InvoiceService = Depends(get_invoice_service),
):
    invoice = service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice
