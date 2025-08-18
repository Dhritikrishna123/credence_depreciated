from __future__ import annotations

from fastapi import Depends, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from ..rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import PlainTextResponse

from ..config import Settings
from ..db import create_session_factory, get_session
from ..schemas import (
    AwardRequest,
    ReverseRequest,
    FlagEvidenceRequest,
    LedgerEntryOut,
    BalanceResponse,
    FlagEvidenceResponse,
    VerificationSetRequest,
    TrustResponse,
    LeaderboardItem,
    LeaderboardResponse,
    LedgerPageResponse,
    DisputeOpenRequest,
    DisputeResolveRequest,
    DisputeOut,
)
from .routers import karma as karma_router
from .routers import trust as trust_router
from .routers import leaderboard as leaderboard_router
from .routers import verification as verification_router
from .routers import balances as balances_router
from .routers import disputes as disputes_router
from .routers import ledger as ledger_router
from .routers import stats as stats_router


def get_settings() -> Settings:
	return Settings.from_env_and_file()


def make_app() -> FastAPI:
	settings = get_settings()
	app = FastAPI(title="Credence API", openapi_url="/v1/openapi.json")

	# Ensure pydantic models are fully built for OpenAPI generation
	try:
		AwardRequest.model_rebuild()
		ReverseRequest.model_rebuild()
		FlagEvidenceRequest.model_rebuild()
		LedgerEntryOut.model_rebuild()
		BalanceResponse.model_rebuild()
		FlagEvidenceResponse.model_rebuild()
		VerificationSetRequest.model_rebuild()
		TrustResponse.model_rebuild()
		LeaderboardItem.model_rebuild()
		LeaderboardResponse.model_rebuild()
		LedgerPageResponse.model_rebuild()
		DisputeOpenRequest.model_rebuild()
		DisputeResolveRequest.model_rebuild()
		DisputeOut.model_rebuild()
	except Exception:
		pass

	# Prepare DB
	session_factory = create_session_factory(settings)

	# Optional OpenTelemetry tracing
	try:
		from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore[import-not-found]
		from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor  # type: ignore[import-not-found]
		FastAPIInstrumentor().instrument_app(app)
		try:
			from sqlalchemy import create_engine as _create_engine  # noqa: F401
			SQLAlchemyInstrumentor().instrument()
		except Exception:
			pass
	except Exception:
		pass

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
	app.add_middleware(SlowAPIMiddleware)

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
	app.include_router(ledger_router.router, prefix="/v1")
	app.include_router(stats_router.router, prefix="/v1")

	return app


app = make_app()


