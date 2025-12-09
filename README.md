# GoIT Python Web Contacts REST API 

A FastAPI service for managing contacts with authentication (JWT) and optional Redis caching.

## Prerequisites

- Python 3.11+ and pip
- Optional: Docker and Docker Compose

## Quickstart (local)

1) Create and activate a virtual environment

- Windows (PowerShell):
  - `python -m venv .venv`
  - `.venv\Scripts\Activate.ps1`
- macOS/Linux:
  - `python3 -m venv .venv`
  - `source .venv/bin/activate`

2) Install dependencies

- `pip install -r requirements.txt`

3) Configure environment

- Copy `.env.example` to `.env` and adjust values.
- Local Postgres via Docker Compose (recommended):
  - `DATABASE_URL=postgresql://user:password@localhost:5433/contacts_db`
- If `DATABASE_URL` is not set, the default above is used by the app.

4) Start the API

- `uvicorn app.main:app --reload`
- Swagger UI: http://127.0.0.1:8000/docs

## Docker Compose (optional)

- `docker-compose up --build`
- This starts Postgres, Redis, and the API. The API reads variables from `.env` and uses `REDIS_URL=redis://redis:6379/0` inside the compose network.

## Documentation (Sphinx)

1) Install docs deps

- `pip install -r docs/requirements.txt`

2) Build HTML docs

- `sphinx-build -b html docs docs/_build`
- Open `docs/_build/index.html`

Notes
- During doc builds, `docs/conf.py` sets `SPHINX_BUILD=True` and mocks heavy imports to avoid DB/Redis connections.

## Tests

The test suite uses SQLite by default and does not require Postgres.

- Run all tests: `PYTHONPATH=. pytest`
- With coverage: `PYTHONPATH=. pytest --cov=app --cov-report=term-missing`

## Environment Variables

- `DATABASE_URL` – Database connection string
- `SECRET_KEY` – JWT signing key
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` – For avatar uploads
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` – For email sending
- `REDIS_URL` – Redis connection string (optional)

See `.env.example` for a minimal template.