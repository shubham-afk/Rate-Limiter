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

**Phase 0 — setup and design.** No limiter behavior is considered implemented until its corresponding phase is complete.
