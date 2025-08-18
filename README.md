Credence — A Pluggable Karma & Trust Engine

Overview

Credence is a standalone, configurable microservice for karma point management, trust score calculation, user verification, and audit-proof reputation tracking.

Features

- Karma management with an append-only ledger (award, reverse, flag)
- Trust and influence computation via pluggable formulas
- Evidence handling and validation via pluggable validators
- Verification providers (external and internal) via plugins
- Dispute workflow (scaffolded), exportable history
- Leaderboards and analytics (time-bounded)
- Pluggable authentication providers (NoAuth, JWT, Internal)

Quick start

1. Create and activate a Python 3.11 environment.
2. Start PostgreSQL: `docker-compose up -d postgres`.
3. Install: `pip install -e .` (development) or `pip install .`.
4. Run the API: `uvicorn credence.api.main:app --reload`.

Configuration

- Settings are powered by pydantic-settings and an optional YAML config.
- Environment: `CREDENCE_CONFIG=./config/config.yaml`.
- See `config/config.example.yaml` for an example.

Development

- Format: `black .` and `isort .`
- Type check: `mypy .`

Notes

- Default auth provider is NoAuth: use `X-User-Id` header to emulate a user.
- Database defaults to PostgreSQL DSN `postgresql+psycopg://credence:credence@localhost:5432/credence`.
  - Override via `DATABASE_URL` env or YAML `database_url`.


API overview
------------

- Base URL: `http://localhost:8000/v1`
- OpenAPI: `GET /v1/openapi.json`
- Metrics: `GET /metrics`
- Health: `GET /healthz`

Auth
- Default: NoAuth provider — include `X-User-Id: <user-id>` header.
- JWT provider (optional): set `plugins.auth_provider` to `credence.auth_providers.jwt_auth:JwtAuthProvider` and configure `jwks_url`, `jwt_issuer`, `jwt_audience`.

Idempotency
- For mutating endpoints, you can send `Idempotency-Key: <unique-key>` to safely retry.

Endpoints (examples)
- POST `/karma/award`

```bash
curl -X POST http://localhost:8000/v1/karma/award \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: alice' \
  -H 'Idempotency-Key: k-123' \
  -d '{"domain":"posts","action":"upvote","evidence_ref":"warn:manual","meta":{"geo":"US"}}'
```

- POST `/karma/reverse`

```bash
curl -X POST http://localhost:8000/v1/karma/reverse \
  -H 'Content-Type: application/json' -H 'X-User-Id: alice' \
  -d '{"entry_id": 42}'
```

- POST `/karma/flag`

```bash
curl -X POST http://localhost:8000/v1/karma/flag \
  -H 'Content-Type: application/json' \
  -d '{"entry_id": 42, "status": "yellow"}'
```

- GET `/balances/{user_id}?domain=posts`

```bash
curl http://localhost:8000/v1/balances/alice?domain=posts
```

- GET `/trust/{user_id}?domain=posts`

```bash
curl http://localhost:8000/v1/trust/alice?domain=posts
```

- GET `/leaderboard?domain=posts&since_days=30&mode=trust_weighted`

```bash
curl "http://localhost:8000/v1/leaderboard?domain=posts&since_days=30&mode=trust_weighted"
```

- GET `/ledger/{user_id}?page=1&page_size=50&domain=posts`

```bash
curl "http://localhost:8000/v1/ledger/alice?page=1&page_size=50&domain=posts"
```

- GET `/ledger/export?format=csv&user_id=alice&domain=posts`

```bash
curl "http://localhost:8000/v1/ledger/export?format=csv&user_id=alice&domain=posts"
```

- GET `/stats`

```bash
curl http://localhost:8000/v1/stats
```


Running with Docker Compose
---------------------------

1. Start dependencies + services:

```bash
docker-compose up -d postgres redis
docker-compose up --build api worker
```

2. Run migrations (from your host or a temporary container):

```bash
alembic upgrade head
# or inside an image:
docker run --rm --net host -v $(pwd):/app -w /app <your-image> alembic upgrade head
```


Migrations
----------

- `0001_initial`: ledger, verifications, idempotency keys
- `0002_disputes`: disputes table
- `0003_append_only_ledger`: append-only triggers on `ledger_entries`
- `0004_trust_and_meta`: `ledger_entries.meta`, `trust_scores`, `evidence_flags`


Plugins
-------

- Trust formula: `plugins.trust_formula` (default: linear)
- Evidence validator: `plugins.evidence_validator` (default: heuristic green/yellow/red)
- Verification provider: `plugins.verification_provider` (default: max external/internal)
- Decay policy: `plugins.decay_policy` (default: no-op)
- Leaderboard strategy: `plugins.leaderboard_strategy` (default: sort desc)
- Auth provider: `plugins.auth_provider` (default: NoAuth)


