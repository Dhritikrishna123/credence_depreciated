from __future__ import annotations

from fastapi import Depends, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from ..rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from fastapi.responses import PlainTextResponse

from ..config import Settings
from ..db import create_session_factory, get_session
from .routers import karma as karma_router
from .routers import trust as trust_router
from .routers import leaderboard as leaderboard_router
from .routers import verification as verification_router
from .routers import balances as balances_router
from .routers import disputes as disputes_router


def get_settings() -> Settings:
	return Settings.from_env_and_file()


def make_app() -> FastAPI:
	settings = get_settings()
	app = FastAPI(title="Credence API", openapi_url="/v1/openapi.json")

	# Prepare DB
	session_factory = create_session_factory(settings)

	@app.get("/healthz")
	def healthz() -> dict[str, str]:
		return {"status": "ok"}

	@app.get("/version")
	def version() -> dict[str, str]:
		return {"version": "0.1.0"}

	# Example dependency usage
	# Routers
	# Instrument metrics
	Instrumentator().instrument(app).expose(app, endpoint="/metrics")

	# Rate limiter
	app.state.limiter = limiter

	@app.exception_handler(RateLimitExceeded)
	def ratelimit_handler(request, exc):  # type: ignore[no-untyped-def]
		return PlainTextResponse("Too Many Requests", status_code=429)

	# Versioned API
	app.include_router(karma_router.router, prefix="/v1")
	app.include_router(trust_router.router, prefix="/v1")
	app.include_router(leaderboard_router.router, prefix="/v1")
	app.include_router(verification_router.router, prefix="/v1")
	app.include_router(balances_router.router, prefix="/v1")
	app.include_router(disputes_router.router, prefix="/v1")

	return app


app = make_app()


