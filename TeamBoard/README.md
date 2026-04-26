# TeamBoard

TeamBoard is a small Django + Django REST Framework (DRF) service that provides:

- Company registration + login (JWT auth)
- A searchable Knowledge Base (KB)
- Query logging per company
- An admin-only usage summary endpoint

All API routes are mounted under the `/api/` prefix.

---

## Prerequisites

- Python 3.x
- pip

---

## Quickstart (local)

From the TeamBoard folder:

```bash
cd /workspaces/Airtribe/TeamBoard
```

Create + activate a virtual environment (optional but recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply migrations:

```bash
python manage.py migrate
```

Seed Knowledge Base entries:

```bash
python manage.py seed_kb
```

Run the server:

```bash
python manage.py runserver
```

- Server: `http://127.0.0.1:8000/`
- API base: `http://127.0.0.1:8000/api/`

---

## Database setup

TeamBoard supports **SQLite by default** and an optional **Postgres (Supabase) connection**.

### Option A — SQLite (default)

No extra configuration is required.

- SQLite file: `TeamBoard/db.sqlite3`

### Option B — Postgres (Supabase)

Create a `.env` file either:

- in `TeamBoard/.env`, or
- in the repo root `.env`

(TeamBoard loads both locations.)

Example `.env`:

```env
USE_SUPABASE_DB=true
SUPABASE_DB_HOST=your-host
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=your-password
SUPABASE_DB_SSLMODE=require
SUPABASE_CONNECT_TIMEOUT=10
```

Then run migrations:

```bash
python manage.py migrate
```

Note: If you are using SQLite, you will NOT see data in PGAdmin.

---

## Django Admin (optional)

Create a Django superuser:

```bash
python manage.py createsuperuser
```

Admin UI:

- `http://127.0.0.1:8000/admin/`

---

## Authentication

This project uses **JWT access tokens** via `djangorestframework-simplejwt`.

- Public endpoints: register + login
- Protected endpoints: KB query, usage summary

To call protected endpoints, include the header:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

---

## API Endpoints

Base URL (local): `http://127.0.0.1:8000`

### 1) Register

`POST /api/auth/register/`

Auth: none

Body (JSON):

```json
{
	"username": "acmecorp",
	"password": "applepass123",
	"email": "dev@appleltd.com",
	"company_name": "Apple Ltd"
}
```

Response (201): includes `api_key` and `access` (JWT).

### 2) Login

`POST /api/auth/login/`

Auth: none

Body (JSON):

```json
{
	"username": "acmecorp",
	"password": "applepass123"
}
```

Response (200): includes `access` (JWT).

### 3) Knowledge Base Query

`POST /api/kb/query/`

Auth: JWT required

Headers:

```http
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json
```

Body (JSON):

```json
{
	"query": "jwt"
}
```

Behavior:

- Returns `400` if `query` is missing or blank
- Returns `401` if no token is provided
- Returns `200` with `{ "count": 0, "results": [] }` if nothing matches (and still writes a QueryLog row)
- Logs each query to `QueryLog` for the current company

### 4) Admin Usage Summary

`GET /api/admin/usage-summary/`

Auth: JWT required + company role must be `admin`

Headers:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

Response (200):

```json
{
	"total_queries": 2,
	"active_companies": 1,
	"top_search_terms": [
		{"search_team": "jwt", "count": 1},
		{"search_team": "django", "count": 1}
	]
}
```

Expected errors:

- `401` if no token
- `403` if logged-in company role is `client`

Make your company an admin (example):

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from api.models import Company

User = get_user_model()
u = User.objects.get(username="acmecorp")
u.company.role = Company.Role.ADMIN
u.company.save(update_fields=["role"])
```

---

## Seeding KB Entries

The `seed_kb` command inserts at least 10 KB entries across multiple categories.

```bash
python manage.py seed_kb
```

It is safe to run multiple times.

---

## Postman

If you have an exported Postman collection file, you can import it in Postman:

- Postman → Import → Select file

This repo currently contains a sample export file:

- `postman_collection.json`

---

## Troubleshooting

- **404 Not Found**: Make sure you’re calling the correct path including `/api/` and the trailing slash.
	Example: `http://127.0.0.1:8000/api/kb/query/`
- **401 Unauthorized**: Missing/invalid JWT. Add `Authorization: Bearer <ACCESS_TOKEN>`.
- **403 Forbidden** on usage summary: Company role is not `admin`.
