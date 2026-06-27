# SubLedger — Low-Level Design

## ERD

```
┌─────────────┐       ┌──────────────────┐
│    Plan     │       │    Customer      │
├─────────────┤       ├──────────────────┤
│ id (PK)     │       │ id (PK)          │
│ name        │       │ name             │
│ description │       │ email (unique)   │
│ price       │       │ created_at       │
│ currency    │ 1     │ updated_at       │
│ billing_cycle│──────│                  │
│ is_active   │       │                  │
│ created_at  │       │                  │
│ updated_at  │       │                  │
└─────────────┘       └────────┬─────────┘
       │                       │
       │                       │
       │ 1                     │ 1
       │                       │
       ▼                       ▼
┌──────────────────────┐       │
│    Subscription      │       │
├──────────────────────┤       │
│ id (PK)              │       │
│ plan_id (FK)         │       │
│ customer_id (FK) ────┼───────┘
│ status               │
│ current_period_start │
│ current_period_end   │
│ created_at           │
│ updated_at           │
└──────────┬───────────┘
           │
           │ 1
           │
           ▼
┌──────────────────────────┐
│        Invoice           │
├──────────────────────────┤
│ id (PK)                  │
│ subscription_id (FK)     │
│ customer_id (FK)         │
│ amount_due               │
│ amount_paid              │
│ currency                 │
│ status                   │
│ period_start             │
│ period_end               │
│ due_date                 │
│ created_at               │
│ updated_at               │
└──────────┬───────────────┘
           │
           │ 1
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌──────────┐ ┌──────────────────┐
│Payment   │ │  LedgerEntry     │
│Attempt   │ ├──────────────────┤
├──────────┤ │ id (PK)          │
│ id (PK)  │ │ invoice_id (FK)  │
│invoice_id│ │ subscribtion_id  │
│ amount   │ │ customer_id (FK) │
│ currency │ │ entry_type       │
│ status   │ │ amount           │
│provider_ │ │ currency         │
│ reference │ │ description      │
│ failure_ │ │ reference_id     │
│ reason   │ │ created_at       │
│created_at│ └──────────────────┘
└──────────┘
```

## Service Layer

| Service | Responsibility |
|---|---|
| `PlanService` | Create, update, list plans. Enforces price > 0 via schema validation. |
| `CustomerService` | Create, get, list customers. Enforces unique email constraint. |
| `SubscriptionService` | Create, get, list, cancel subscriptions. Enforces active-plan and no-duplicate-active rules. |
| `InvoiceService` | Generate invoices with amount_due from plan price. Creates ledger entries on generation. |
| `PaymentService` | Record payment attempts, update invoice status, enforce overpayment protection. Creates ledger entries. |
| `LedgerService` | Append-only entry creation and querying by customer/invoice/type. |

## Repository Layer (Data Access)

| Repository | Methods |
|---|---|
| `PlanRepository` | `create`, `get_by_id`, `get_all` (with inactive filter), `update` |
| `CustomerRepository` | `create`, `get_by_id`, `get_by_email`, `get_all` |
| `SubscriptionRepository` | `create`, `get_by_id`, `get_all` (filtered), `get_active_by_customer_and_plan`, `update` |
| `InvoiceRepository` | `create`, `get_by_id`, `get_all` (filtered), `update` |
| `PaymentAttemptRepository` | `create`, `get_by_id`, `get_by_invoice_id` |
| `LedgerRepository` | `create`, `get_by_id`, `get_all` (filtered by customer/invoice/type) |

## Business Rule Ownership

| Business Rule | Owned By | Enforcement Layer |
|---|---|---|
| Plan price must be > 0 | `PlanService` | Schema (`Field(gt=0)`) + DB constraint |
| Customer email must be unique | `CustomerService` | Schema (`EmailStr`) + DB unique constraint |
| Cannot create subscription for inactive plan | `SubscriptionService` | Service logic |
| Customer cannot have 2 active subscriptions to same plan | `SubscriptionService` | Service query |
| Invoice amount_due from plan price at generation | `InvoiceService` | Service logic |
| Successful payment cannot exceed remaining unpaid | `PaymentService` | Service validation |
| Full payment → paid; partial → partially_paid | `PaymentService` | Service logic |
| Failed payment doesn't increase amount_paid | `PaymentService` | Service logic (only update on success) |
| Ledger entries append-only, traceable by reference_id | `LedgerService` | Repository (no update/delete methods exposed) |

## Architecture Pattern

**Layered Architecture (Route → Service → Repository) + Dependency Injection**

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌─────────┐
│  Route   │────>│ Service  │────>│  Repository  │────>│   DB    │
│ (API)    │     │ (Biz     │     │  (Data       │     │(SQLite/ │
│          │     │  Logic)  │     │   Access)    │     │ Postgres)│
└──────────┘     └──────────┘     └──────────────┘     └─────────┘
```

- **Routes** handle HTTP concerns: parsing requests, returning responses, dependency injection wiring.
- **Services** own all business rules and orchestration logic. They compose multiple repositories when needed.
- **Repositories** encapsulate all SQLAlchemy queries. No business logic lives here.
- **Dependency Injection** via FastAPI's `Depends()` keeps each layer testable in isolation.

This follows the **Repository Pattern** for data access separation and the **Service Layer** pattern for business logic isolation.

## Core Flows

### Invoice Generation Flow

```
1. POST /api/v1/invoices { subscription_id }
2. InvoiceService.generate_invoice(subscription_id)
3.   ├─ SubscriptionRepository.get_by_id(subscription_id)
4.   ├─ Validate: subscription exists AND status is "active"
5.   ├─ PlanRepository.get_by_id(subscription.plan_id)
6.   ├─ Calculate: amount_due = plan.price
7.   ├─ InvoiceRepository.create(invoice)
8.   └─ LedgerService.create_entry(invoice_created, ...)
9. Return InvoiceResponse
```

### Payment Recording Flow

```
1. POST /api/v1/payments { invoice_id, amount, status, ... }
2. PaymentService.record_payment(data)
3.   ├─ InvoiceRepository.get_by_id(invoice_id)
4.   ├─ Validate: invoice exists
5.   ├─ PaymentAttemptRepository.create(attempt)
6.   ├─ If status == "failed":
7.   │    ├─ Do NOT update amount_paid
8.   │    └─ LedgerService.create_entry(payment_failure, ...)
9.   ├─ Else (success):
10.  │    ├─ Validate: amount <= remaining (amount_due - amount_paid)
11.  │    ├─ Update: invoice.amount_paid += amount
12.  │    ├─ If amount_paid >= amount_due → status = "paid"
13.  │    ├─ Else → status = "partially_paid"
14.  │    └─ LedgerService.create_entry(payment_success, ...)
15. Return PaymentResponse + invoice_status
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/plans` | Create a plan |
| GET | `/api/v1/plans` | List plans (optional `?include_inactive=true`) |
| GET | `/api/v1/plans/{id}` | Get plan by ID |
| PATCH | `/api/v1/plans/{id}` | Update plan |
| POST | `/api/v1/customers` | Create a customer |
| GET | `/api/v1/customers` | List customers |
| GET | `/api/v1/customers/{id}` | Get customer by ID |
| POST | `/api/v1/subscriptions` | Create a subscription |
| GET | `/api/v1/subscriptions` | List subscriptions |
| GET | `/api/v1/subscriptions/{id}` | Get subscription by ID |
| POST | `/api/v1/subscriptions/{id}/cancel` | Cancel a subscription |
| POST | `/api/v1/invoices` | Generate an invoice |
| GET | `/api/v1/invoices` | List invoices |
| GET | `/api/v1/invoices/{id}` | Get invoice by ID |
| POST | `/api/v1/payments` | Record a payment |
| GET | `/api/v1/ledger` | List ledger entries |

## Assumptions & Limitations

1. **No authentication/authorization** — no API keys, JWT, or user sessions.
2. **No webhooks** — external payment providers not integrated.
3. **No proration** — invoices are always the full plan price.
4. **Billing periods** — subscriptions default to 30-day cycles; no custom billing intervals.
5. **Single currency per invoice** — derived from the plan's currency.
6. **No invoice due date enforcement** — due_date is set but no automated dunning.
7. **No concurrency handling** — optimistic locking not implemented; assumes serial access per resource.
8. **No soft deletes** — records are hard-deleted only through drops; ledger is truly append-only.
