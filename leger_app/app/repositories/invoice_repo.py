from sqlalchemy.orm import Session

from app.models.invoice import Invoice


class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.flush()
        return invoice

    def get_by_id(self, invoice_id: int) -> Invoice | None:
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

    def get_all(
        self,
        subscription_id: int | None = None,
        customer_id: int | None = None,
    ) -> list[Invoice]:
        query = self.db.query(Invoice)
        if subscription_id is not None:
            query = query.filter(Invoice.subscription_id == subscription_id)
        if customer_id is not None:
            query = query.filter(Invoice.customer_id == customer_id)
        return query.all()

    def update(self, invoice: Invoice) -> Invoice:
        self.db.flush()
        return invoice
