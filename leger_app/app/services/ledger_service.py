from app.models.ledger_entry import LedgerEntry
from app.repositories.ledger_repo import LedgerRepository


class LedgerService:
    def __init__(self, ledger_repo: LedgerRepository):
        self.ledger_repo = ledger_repo

    def create_entry(
        self,
        entry_type: str,
        customer_id: int,
        amount: float,
        currency: str = "INR",
        invoice_id: int | None = None,
        subscription_id: int | None = None,
        reference_id: str | None = None,
        description: str | None = None,
    ) -> LedgerEntry:
        """Create an append-only ledger entry. Ledger entries are immutable
        once created — we never update or delete them."""
        entry = LedgerEntry(
            invoice_id=invoice_id,
            subscription_id=subscription_id,
            customer_id=customer_id,
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            description=description,
            reference_id=reference_id,
        )
        return self.ledger_repo.create(entry)

    def list_entries(
        self,
        customer_id: int | None = None,
        invoice_id: int | None = None,
        entry_type: str | None = None,
    ) -> list[LedgerEntry]:
        return self.ledger_repo.get_all(
            customer_id=customer_id,
            invoice_id=invoice_id,
            entry_type=entry_type,
        )
