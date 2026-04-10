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

### Notes
- The database runs in Docker (Postgres). The backend connects using the Compose service hostname `db`.
- Current stock is derived from the movement ledger; the backend rejects movements that would drive stock negative.

### Walkthrough Video
<video src="https://github.com/mdadnankh/Inventory-tracking-app/blob/main/better-software-assignment-walkthrough-MdAdnanKhan.mov?raw=true" width="100%" controls></video>
