from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.customer_repo import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerResponse
from app.services.customer_service import CustomerService

router = APIRouter(tags=["Customers"])


def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    return CustomerService(CustomerRepository(db))


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
):
    return service.create_customer(data)


@router.get("/customers", response_model=list[CustomerResponse])
def list_customers(service: CustomerService = Depends(get_customer_service)):
    return service.list_customers()


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
):
    customer = service.get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
