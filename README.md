# Gatekeeper — Distributed Rate Limiter

Gatekeeper is a standalone rate-limiting service that sits in front of an API. For every request it evaluates a configured rule, then either permits the request to the protected API or rejects it with HTTP `429 Too Many Requests`.

This project is being built in deliberate phases. Phase 0 defines the system boundaries and API before implementation begins.

## Problem statement

Application APIs need consistent, distributed request limits across multiple gateway instances. In-process counters cannot meet that need: their state is isolated per instance and is vulnerable to concurrency races. Gatekeeper will use Redis as its shared, atomic decision state; PostgreSQL will hold durable rate-limit rules and request-event history.

## Locked stack

| Area | Choice |
| --- | --- |
| Backend | Python 3.12 + Django 5.1 (project: `backend/`) |
| API style | Django JSON endpoints; OpenAPI 3.1 contract |
| Realtime | Django Channels + Redis channel layer (Phase 5) |
| Shared limiter state / cache | Redis 7 + `redis-py` |
| Durable data | PostgreSQL 16 + Django ORM + `psycopg` |
| Frontend | React 18 + TypeScript + Vite (project: `frontend/`) |
| Charts | Recharts |
| Local environment | Docker Compose |
| Load tests | k6 |

The service will implement fixed-window, sliding-window-log, token-bucket, and sliding-window-counter algorithms. The initial production-oriented algorithm will be token bucket; each rule selects its own algorithm.

## Repository layout

```text
backend/                  Django API and rate-limiter service
frontend/                 React dashboard (introduced in its phase)
docs/
  api-contract.yaml       OpenAPI contract — source of truth
  architecture.drawio     Editable draw.io diagram
  architecture.md         Renderable architecture overview
```

## Architecture

The editable source is [docs/architecture.drawio](docs/architecture.drawio). A rendered, text-friendly overview is in [docs/architecture.md](docs/architecture.md).

## API contract

The source of truth is [docs/api-contract.yaml](docs/api-contract.yaml). The initially defined endpoints are:

- `POST /admin/keys` — create an API key and its rate-limit rule
- `GET` / `PUT /admin/keys/{key}` — inspect or update a rule and usage
- `POST /check` — make a limiter decision without proxying
- `GET /api/data` — protected demonstration endpoint
- `GET /metrics` — aggregate allowed/denied counts
- `WS /live` — future live request-event stream

## Phases

1. Fixed-window limiting in one Django instance.
2. Redis-backed atomic state and multi-instance correctness.
3. Additional algorithms and rule selection.
4. API-key, tier, endpoint, IP, and user scoping with PostgreSQL rules.
5. React dashboard, metrics, and live updates.
6. k6 load tests, documented results, and optional horizontal scaling.

## Development status

**Phase 2 — distributed Redis limiter.** `/api/data` is protected by rules in PostgreSQL, cached in Redis, and enforced atomically by Redis Lua scripts across every gateway instance. Fixed window, token bucket, and sliding-window-counter rules are available. Sliding-window-log remains a planned Phase 3 algorithm.

**Phase 3 — persisted configuration and logging.** API credentials live separately from their rules; unauthenticated clients can be constrained by a persisted IP fallback rule. Request events are appended to a Redis queue and persisted by the `event_worker` service, keeping PostgreSQL writes out of the decision path.

## Phase 1 local demo

## Phase 2 distributed demo

Start the two gateway instances, shared Redis, Postgres, and Nginx load balancer:

```bash
docker compose up --build
```

Create a rule through the Nginx entry point:

```bash
curl -X POST http://localhost:8000/admin/keys -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-development-admin-token" \
  -d '{"name":"demo","key":"demo-key","algorithm":"fixed_window","limit":100,"windowSeconds":60}'
```

Then send requests with an API key:

```bash
for i in {1..105}; do
  curl -s -o /dev/null -w "%{http_code}\n" -H "X-API-Key: demo-key" http://localhost:8000/api/data
done
```

The first 100 responses are `200`; the remaining five are `429`. On PowerShell, use:

```powershell
1..105 | ForEach-Object { (Invoke-WebRequest http://localhost:8000/api/data -Headers @{ 'X-API-Key' = 'demo-key' } -SkipHttpErrorCheck).StatusCode }
```

To create a repeatable race-condition proof, run this while the Compose services are running:

```bash
docker compose exec backend_1 python manage.py demonstrate_race
```

It prints two `True` results from the deliberately unsafe `GET → check → SET` code at a limit of one, then one `True` and one `False` from the atomic Lua script. Capture that terminal output in your README/screenshots when you run the demo.

Run the tests with `python manage.py test limiter`. The Phase 1 boundary-burst test intentionally proves that a fixed window allows 200 requests around a 60-second boundary.

`ADMIN_API_TOKEN` protects rule-management endpoints. Docker Compose uses `local-development-admin-token` only as a local default. Set a strong secret in your environment before deploying, for example: `ADMIN_API_TOKEN=... docker compose up --build`.

### Phase 3 IP fallback

Configure a persisted limit for requests that have no `X-API-Key` header:

```powershell
$fallback = @{ name = "anonymous"; algorithm = "fixed_window"; limit = 10; windowSeconds = 60 } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Put -Uri "http://localhost:8000/admin/rules/ip-fallback" -ContentType "application/json" -Headers @{ Authorization = "Bearer local-development-admin-token" } -Body $fallback
```

The Nginx proxy forwards the client address; unauthenticated calls to `/api/data` share an IP-scoped counter. The `event_worker` service consumes Redis queue events and inserts `RequestLog` records in PostgreSQL asynchronously.
