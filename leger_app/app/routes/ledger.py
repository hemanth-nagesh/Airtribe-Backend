from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.ledger_repo import LedgerRepository
from app.schemas.ledger_entry import LedgerEntryResponse
from app.services.ledger_service import LedgerService

router = APIRouter(tags=["Ledger"])


def get_ledger_service(db: Session = Depends(get_db)) -> LedgerService:
    return LedgerService(LedgerRepository(db))


@router.get("/ledger", response_model=list[LedgerEntryResponse])
def list_ledger_entries(
    customer_id: int | None = None,
    invoice_id: int | None = None,
    entry_type: str | None = None,
    service: LedgerService = Depends(get_ledger_service),
):
    return service.list_entries(
        customer_id=customer_id,
        invoice_id=invoice_id,
        entry_type=entry_type,
    )
