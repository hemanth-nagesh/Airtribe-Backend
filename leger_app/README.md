# SubLedger

A simplified billing backend for managing plans, customers, subscriptions, invoices, payments, and ledger events. Built with FastAPI + SQLAlchemy + PostgreSQL.

## Setup

### Local (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your DATABASE_URL

# Run the app
uvicorn app.main:app --reload
```

### Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

## API

Full API documentation is available at `/docs` when the server is running (auto-generated OpenAPI/Swagger).

**Endpoints:**

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/plans` | Create a plan |
| GET | `/api/v1/plans` | List plans |
| GET | `/api/v1/plans/{id}` | Get plan |
| PATCH | `/api/v1/plans/{id}` | Update plan |
| POST | `/api/v1/customers` | Create a customer |
| GET | `/api/v1/customers` | List customers |
| GET | `/api/v1/customers/{id}` | Get customer |
| POST | `/api/v1/subscriptions` | Create a subscription |
| GET | `/api/v1/subscriptions` | List subscriptions |
| GET | `/api/v1/subscriptions/{id}` | Get subscription |
| POST | `/api/v1/subscriptions/{id}/cancel` | Cancel a subscription |
| POST | `/api/v1/invoices` | Generate an invoice |
| GET | `/api/v1/invoices` | List invoices |
| GET | `/api/v1/invoices/{id}` | Get invoice |
| POST | `/api/v1/payments` | Record a payment |
| GET | `/api/v1/ledger` | List ledger entries |

## Testing

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_payments.py -v
```

Tests use SQLite in-memory, so no external database is needed.

## Project Structure

```
leger_app/
├── app/
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Settings
│   ├── db.py                # DB engine + session
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic request/response
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic
│   └── routes/              # API endpoints
├── tests/                   # Pytest tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── DESIGN.md                # Full LLD documentation
└── README.md
```

## Design

See [DESIGN.md](./DESIGN.md) for the complete low-level design including ERD, service/repository responsibilities, business rule ownership, architecture patterns, and core flows.
