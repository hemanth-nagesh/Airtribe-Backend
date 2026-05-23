# PulseNotify

PulseNotify is a Django + DRF backend that lets users create **flight route price alerts** (e.g., `DEL-BOM` with a threshold). A background Celery job periodically checks current prices and triggers a notification when the price is **at or below** the threshold.

At a high level:

1. Users register / login to get JWT tokens.
2. Users create `priceAlert` records for a route and a `treshold_price`.
3. Celery Beat runs `check_prices()` every minute.
4. For each active alert route, the system fetches the latest price and triggers a `notification` record if `current_price <= treshold_price`.

> Note on naming: the project uses model/field names like `priceAlert`, `treshold_price`, `orign`, `trigered_price_alert` (typos included). The README uses the same names to match the code and database schema.

---

## Tech stack

- Django (project + admin)
- Django REST Framework (API)
- SimpleJWT (JWT auth)
- Celery (background jobs) + Celery Beat (scheduler)
- Redis (Celery broker/result backend)
- PostgreSQL (database)
- A small dummy external HTTP server that provides mock flight prices

---

## Repository structure (what each file does)

### Root

- `manage.py`
  - Django entrypoint. Defaults to `DJANGO_SETTINGS_MODULE=pulsenotify.settings.local`.

- `requirements.txt`
  - Python dependencies.

- `.env.example` / `.env`
  - Environment variables used for DB/Celery configuration.

- `docker-compose.yml`
  - Starts Redis and Postgres containers for local development.

- `External_price_server.py`
  - Dummy external “flight price server” that serves:
    - `GET http://127.0.0.1:8080/api/flights/price/?route=del-bom`
  - Returns JSON like `{ "route": "del-bom", "price": 4321 }`.

- `celerybeat-schedule`
  - Celery Beat local schedule state file (created/updated when Celery Beat runs).

- `Pulsenotify.postman_collection.json`
  - Postman collection to exercise APIs.

- `tests.py`
  - Project-level tests (added for unit testing coverage). Django will also discover tests inside apps.

### `pulsenotify/` (Django project)

- `pulsenotify/settings/base.py`
  - Common settings (installed apps, middleware, REST_FRAMEWORK defaults, Celery config).
  - Defines `CELERY_BEAT_SCHEDULE` to run the periodic price check.

- `pulsenotify/settings/local.py`
  - Local settings. Loads `.env` (if python-dotenv is installed) and configures the database from environment variables.

- `pulsenotify/settings/production.py`
  - Production settings stub.

- `pulsenotify/urls.py`
  - Routes `/api/` to the `user` app.

- `pulsenotify/celery.py`
  - Celery app configuration. Uses the same settings module as Django local config.

- `pulsenotify/task.py`
  - **Business logic** background tasks:
    - `check_prices()` (scheduled every minute): fetches prices for all active alerts and triggers notifications.
    - `send_notification(alert_id, triggered_price)`: creates a `notification` row and marks the alert as `TRIGGERED`.

### `user/` (main application)

- `user/models.py`
  - `UserProfile`: extends the built-in Django `User` with a `role`.
  - `priceAlert`: alert model storing route (`orign`, `destination`), `treshold_price`, and status.
  - `notification`: stores triggered alert messages.

- `user/signals.py`
  - Automatically creates `UserProfile` whenever a Django `User` is created.

- `user/serializers.py`
  - DRF serializer for `priceAlert`.

- `user/permissions.py`
  - `IsAdminUser`: allows access only when `request.user.profile.role == 'admin'`.

- `user/views.py`
  - Auth endpoints:
    - `POST /api/auth/register/`
    - `POST /api/auth/login/`
  - Alerts CRUD (JWT protected) via `PriceAlertViewSet`:
    - `GET/POST /api/alerts/`
    - `GET/PUT/PATCH/DELETE /api/alerts/{id}/`
      - `DELETE` sets alert status to `INACTIVE` instead of deleting the row.
  - `GET /api/admin/summary/` (admin-only)
  - `GET /api/flights/price/` (public): proxies to the external price server.

- `user/urls.py`
  - Defines the REST routes under `/api/`.

- `user/tests.py`
  - Unit tests that validate core business behavior.

---

## Configuration (environment variables)

Create a `.env` file in the project root (same folder as `manage.py`). You can start from `.env.example`.

### Required (local dev)

**Database** (used by `pulsenotify/settings/local.py`):

- `DATABASES_ENGINE` (example: `django.db.backends.postgresql`)
- `DATABASES_NAME` (example: `postgres`)
- `DATABASES_USER` (example: `postgres`)
- `DATABASES_PASSWORD` (example: `postgres`)
- `DATABASES_HOST` (example: `localhost`)
- `DATABASES_PORT` (example: `5432`)

**Celery** (defaults exist in settings, but you usually want to set these explicitly):

- `CELERY_BROKER_URL` (example: `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND` (example: `redis://localhost:6379/0`)

**External price server** (used by `/api/flights/price/`):

- `FLIGHT_PRICE_SERVER_URL`
  - default: `http://127.0.0.1:8080/api/flights/price/`

---

## How to run (local development)

### 1) Start infrastructure (Redis + Postgres)

Option A — using Docker (recommended):

```bash
docker compose up -d
```

This brings up:

- Redis on `localhost:6379`
- Postgres on `localhost:5432` (user/password/db are `postgres` per `docker-compose.yml`)

Option B — run Redis/Postgres manually

If you already have Redis/Postgres locally installed, make sure they are reachable using the host/port values in `.env`.

### 2) Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) Create `.env`

```bash
cp .env.example .env
```

Edit `.env` if needed.

### 4) Run migrations

```bash
python manage.py migrate
```

(Optional) Create a superuser for Django admin:

```bash
python manage.py createsuperuser
```

### 5) Start the dummy flight price server

This simulates an external provider.

```bash
python External_price_server.py
```

By default it listens on `http://127.0.0.1:8080`.

### 6) Start Django API server

```bash
python manage.py runserver 0.0.0.0:8000
```

API base URL: `http://127.0.0.1:8000/api/`

### 7) Start Celery worker and Celery beat

Open **two terminals** (recommended):

Terminal A — worker:

```bash
celery -A pulsenotify worker -l info
```

Terminal B — beat (scheduler):

```bash
celery -A pulsenotify beat -l info
```

Celery Beat schedules `pulsenotify.task.check_prices` every minute (see `CELERY_BEAT_SCHEDULE` in settings).

---

## API overview

All routes are under `/api/` (see `pulsenotify/urls.py`).

### Authentication

- `POST /api/auth/register/`
  - body: `{ "username": "...", "email": "...", "password": "..." }`
  - returns: JWT `refresh` + `access` token

- `POST /api/auth/login/`
  - body: `{ "username": "...", "password": "..." }`
  - returns: JWT `refresh` + `access` token

JWT is expected as:

```
Authorization: Bearer <access_token>
```

### Alerts (JWT required)

- `GET /api/alerts/`
  - returns only alerts belonging to the authenticated user (scoped by `get_queryset`).

- `POST /api/alerts/`
  - body (example):
    ```json
    {
      "orign": "DEL",
      "destination": "BOM",
      "treshold_price": 4500
    }
    ```

- `DELETE /api/alerts/{id}/`
  - does **not** delete the row; sets `status` to `inactive`.

### Price endpoint (public)

- `GET /api/flights/price/?route=DEL-BOM`
- `GET /api/flights/price/DEL-BOM/`

These endpoints **proxy** to the external price server defined by `FLIGHT_PRICE_SERVER_URL`.

### Admin summary (admin role required)

- `GET /api/admin/summary/`

Requires the user’s profile role to be `admin` (checked by `user/permissions.py:IsAdminUser`).

---

## How alert triggering works

1. `check_prices()` (Celery task) finds all active alerts.
2. For each `(orign, destination)` route, it calls the local API `GET /api/flights/price/?route=<route>`.
3. The API endpoint calls the external price server (dummy server by default) and returns the current price.
4. For each alert on that route:
   - if `float(current_price) <= float(alert.treshold_price)`, it triggers `send_notification.delay(alert.id, current_price)`.
5. `send_notification()` writes a `notification` row and marks the alert `TRIGGERED` so it doesn’t fire repeatedly.

---

## Running tests

```bash
python manage.py test
```

Business-logic unit tests exist in:

- `user/tests.py`
- `tests.py`

---

## Common troubleshooting

- **Database ENGINE is missing / ImproperlyConfigured**
  - Ensure your `.env` sets `DATABASES_ENGINE` and other `DATABASES_*` values.

- **Celery can’t connect to Redis**
  - Confirm Redis is running and `CELERY_BROKER_URL` is correct.
  - If using Docker, run `docker compose up -d`.

- **`/api/flights/price/` returns “Price server unavailable”**
  - Start the dummy price server (`python External_price_server.py`) or set `FLIGHT_PRICE_SERVER_URL` to the correct external endpoint.
