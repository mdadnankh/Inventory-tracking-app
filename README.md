## Inventory Tracker (Ledger-based)

Small Inventory app with **Products**, **Stock Movements**, and **Low-stock Alerts**.

### Requirements
- Docker Desktop (or Docker Engine) with `docker compose`

### Quickstart
From repo root:

```bash
docker compose up --build
```

Then open:
- Frontend: `http://localhost:5173`
- API health: `http://localhost:5001/api/health`

### API endpoints (MVP)
- `GET /api/products`
- `POST /api/products`
- `PATCH /api/products/:id`
- `GET /api/products/:id/movements`
- `POST /api/products/:id/movements`
- `GET /api/alerts/low-stock`

### Useful commands
- **Seed demo data**:

```bash
docker compose run --rm backend python -m app.scripts.seed
```

- **Run backend tests**:

```bash
docker compose run --rm backend pytest
```

- **Reset DB** (deletes all local data):

```bash
docker compose down -v
```

### Key Technical Decisions
- **Append-Only Ledger for Stock:** Instead of mutating an absolute `current_stock` integer directly (which invites race conditions and lost history), this system dynamically derives current stock entirely from a log of events. This guarantees correctness and provides a free, un-forgeable audit log.
- **Strict Data Boundaries (Pydantic):** Incoming JSON requests are heavily validated via Pydantic schemas (e.g. enforcing positive numbers and conditional 'adjust direction' fields) *before* they ever interact with the ORM or database layer. This ensures the backend handles zero malformed data.
- **Cursor Pagination:** The movement history uses cursor-based pagination. Because ledgers are append-only chronologically, looking up older rows via IDs (`id < cursor`) guarantees stable, skip-free paginated reads even while new events are actively being written.
- **Database-delegated Invariants:** Complex logic, like grouping products and filtering low-stock alerts, is explicitly offloaded to the PostgreSQL query engine (using `OUTER JOIN`, `SUM(case...)`, and `HAVING` clauses) rather than piping arrays into Python memory. 
- **Standardized Error Contracts:** All Flask errors inherit from a custom `ApiError`, ensuring the frontend receives a 100% predictable JSON structure (`code`, `message`, `details`) making failures instantly observable and diagnosable.

### Notes
- The database runs in Docker (Postgres). The backend connects using the Compose service hostname `db`.
- Current stock is derived from the movement ledger; the backend rejects movements that would drive stock negative.

### Walkthrough Video
**[👉 Click here to watch the full 10-15 minute Walkthrough Video natively on GitHub](https://github.com/mdadnankh/Inventory-tracking-app/blob/main/better-software-assignment-walkthrough-MdAdnanKhan.mov)**
