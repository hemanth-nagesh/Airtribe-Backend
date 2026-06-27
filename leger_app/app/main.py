from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
from app.routes import plans, customers, subscriptions, invoices, payments, ledger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SubLedger",
    description="A simplified billing backend for managing plans, customers, subscriptions, invoices, payments, and ledger events.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(plans.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(subscriptions.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(ledger.router, prefix="/api/v1")
