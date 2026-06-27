from fastapi import HTTPException

from app.models.customer import Customer
from app.repositories.customer_repo import CustomerRepository
from app.schemas.customer import CustomerCreate


class CustomerService:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    def create_customer(self, data: CustomerCreate) -> Customer:
        existing = self.customer_repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Customer with email '{data.email}' already exists",
            )
        customer = Customer(name=data.name, email=data.email)
        return self.customer_repo.create(customer)

    def get_customer(self, customer_id: int) -> Customer | None:
        return self.customer_repo.get_by_id(customer_id)

    def list_customers(self) -> list[Customer]:
        return self.customer_repo.get_all()
