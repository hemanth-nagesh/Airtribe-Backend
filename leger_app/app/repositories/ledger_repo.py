from sqlalchemy.orm import Session

from app.models.ledger_entry import LedgerEntry


class LedgerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, entry: LedgerEntry) -> LedgerEntry:
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_by_id(self, entry_id: int) -> LedgerEntry | None:
        return (
            self.db.query(LedgerEntry).filter(LedgerEntry.id == entry_id).first()
        )

    def get_all(
        self,
        customer_id: int | None = None,
        invoice_id: int | None = None,
        entry_type: str | None = None,
    ) -> list[LedgerEntry]:
        query = self.db.query(LedgerEntry)
        if customer_id is not None:
            query = query.filter(LedgerEntry.customer_id == customer_id)
        if invoice_id is not None:
            query = query.filter(LedgerEntry.invoice_id == invoice_id)
        if entry_type is not None:
            query = query.filter(LedgerEntry.entry_type == entry_type)
        return query.order_by(LedgerEntry.created_at.asc()).all()
