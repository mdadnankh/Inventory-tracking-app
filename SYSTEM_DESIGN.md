## System design (Inventory Tracker)

### Overview
A small internal tool to manage **Products** and track stock using an **append-only movement ledger**. Current stock is derived from movements, making the system auditable and resilient to change.

### Goals
- **Correctness**: prevent invalid states (notably negative stock)
- **Simplicity**: clear boundaries, minimal abstractions
- **Reproducible runtime**: one-command startup using Docker Compose
- **Verification**: automated tests for key invariants

---

## Architecture

### Runtime components
- **Frontend**: React + Vite (served on `:5173`)
- **Backend API**: Flask + Gunicorn (published as `:5001` → container `:5000`)
- **Database**: PostgreSQL (container-only, not published to host)

### Networking
- Browser talks to frontend at `http://localhost:5173`
- Frontend calls API under `/api/*` and Vite proxies it to the backend container.
- Backend connects to Postgres using the Compose hostname `db`:
  - `postgresql+psycopg://app:app@db:5432/app`

---

## Domain model

### Product
Represents a stocked item.

Key fields:
- `sku` (**unique**)
- `name`
- `low_stock_threshold`

### StockMovement (ledger)
Represents a stock change. This is the source of truth.

Types:
- `receive` \(+\)
- `ship` \(-\)
- `adjust` \(+\) or \(-\) using `direction` (`increase|decrease`)

### Derived current stock
\[
\text{stock} = \sum(receive) - \sum(ship) \pm \sum(adjust)
\]

---

## Correctness rules (invariants)

Enforced in the backend:
- **Unique SKU**: conflicts return HTTP 409
- **Movement validation**:
  - `quantity >= 1`
  - `type ∈ {receive, ship, adjust}`
  - `direction` required iff `type=adjust`
- **No negative stock**:
  - movement creation is rejected if it would make the derived stock < 0

---

## Database schema (Postgres)

### Tables
- `products`
  - `id` (int PK)
  - `sku` (varchar, unique)
  - `name` (varchar)
  - `low_stock_threshold` (int)
  - timestamps

- `stock_movements`
  - `id` (int PK)
  - `product_id` (FK → products)
  - `type` enum (`receive|ship|adjust`)
  - `direction` enum (`increase|decrease`, nullable)
  - `quantity` int
  - `note` text nullable
  - `created_at`

### Migrations
Alembic creates the schema on container startup:
- `backend/migrations/versions/0001_init.py`

---

## Backend design (Flask)

### Structure
- `backend/app/api/`: HTTP routes + request parsing
  - `products.py`: products + movements, includes cursor pagination for movement history
  - `alerts.py`: low-stock endpoint
  - `errors.py`: consistent error shape
- `backend/app/db/`: SQLAlchemy engine/session + models
- `backend/migrations/`: Alembic migrations
- `backend/tests/`: pytest API tests

### API shape (MVP)
- `GET /api/health`
- `GET /api/products`
- `POST /api/products`
- `PATCH /api/products/:id`
- `GET /api/products/:id/movements?limit=20&cursor=<id>`
  - Returns `{ items: [...], next_cursor: <id|null> }`
- `POST /api/products/:id/movements`
- `GET /api/alerts/low-stock`

### Pagination
Movement history uses **cursor pagination** based on `stock_movements.id`:
- First page: `GET .../movements?limit=20`
- Next page: `GET .../movements?limit=20&cursor=<next_cursor>`

This is stable and efficient for append-only ledgers.

---

## Frontend design (React + Tailwind)

### UI goals
- Clear information hierarchy (products → movements → alerts)
- Fast feedback on validation/invariant errors
- Professional look with minimal components

### Styling
Tailwind CSS is used for a polished, consistent UI:
- config: `frontend/tailwind.config.js`, `frontend/postcss.config.js`
- global CSS: `frontend/src/index.css`

---

## Seed / dummy data

To load deterministic demo data into Postgres:

```bash
docker compose run --rm backend python -m app.scripts.seed
```

This truncates tables and inserts:
- 5 sample products
- randomized movement history (with stock kept non-negative)

---

## Verification

Backend tests prove core invariants:

```bash
docker compose run --rm backend pytest -q
```

Tests cover:
- unique SKU conflict
- stock math (receive)
- no-negative-stock enforcement
- low-stock alerts
