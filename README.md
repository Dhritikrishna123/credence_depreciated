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
2. Install: `pip install -e .` (development) or `pip install .`.
3. Run the API: `uvicorn credence.api.main:app --reload`.

Configuration

- Settings are powered by pydantic-settings and an optional YAML config.
- Environment: `CREDENCE_CONFIG=./config/config.yaml`.
- See `config/config.example.yaml` for an example.

Development

- Format: `black .` and `isort .`
- Type check: `mypy .`

Notes

- Default auth provider is NoAuth: use `X-User-Id` header to emulate a user.
- Database defaults to SQLite at `./credence.db`. Configure via `DATABASE_URL` env or YAML.


