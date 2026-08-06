# Architecture overview

```mermaid
flowchart LR
    C[API client] --> G[Gatekeeper rate-limiter service]
    G -->|allowed| D[Dummy backend API]
    G -->|denied: HTTP 429| C
    G <--> R[(Redis\nshared atomic state\n& hot rule cache)]
    G -. async request events .-> P[(PostgreSQL\nrules & analytics)]
    UI[React dashboard] -->|REST / WebSocket| G
```

Request decisions are synchronous and must be atomic in Redis. Persisting analytics must never delay a decision; event logging will therefore be asynchronous. PostgreSQL is authoritative for rate-limit rules, while Redis caches hot rules and holds algorithm state.

The protected dummy endpoint is intentionally small. It exists to prove that Gatekeeper can enforce a rule before work reaches an upstream API.
