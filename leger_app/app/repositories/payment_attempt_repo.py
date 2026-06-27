from sqlalchemy.orm import Session

from app.models.payment_attempt import PaymentAttempt


class PaymentAttemptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payment_attempt: PaymentAttempt) -> PaymentAttempt:
        self.db.add(payment_attempt)
        self.db.flush()
        return payment_attempt

    def get_by_id(self, payment_attempt_id: int) -> PaymentAttempt | None:
        return (
            self.db.query(PaymentAttempt)
            .filter(PaymentAttempt.id == payment_attempt_id)
            .first()
        )

    def get_by_invoice_id(self, invoice_id: int) -> list[PaymentAttempt]:
        return (
            self.db.query(PaymentAttempt)
            .filter(PaymentAttempt.invoice_id == invoice_id)
            .all()
        )
