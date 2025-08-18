from __future__ import annotations

from fastapi import Depends, FastAPI

from ..config import Settings
from ..db import create_session_factory, get_session
from .routers import karma as karma_router
from .routers import trust as trust_router
from .routers import leaderboard as leaderboard_router
from .routers import verification as verification_router
from .routers import balances as balances_router


def get_settings() -> Settings:
	return Settings.from_env_and_file()


def make_app() -> FastAPI:
	settings = get_settings()
	app = FastAPI(title="Credence API")

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
	app.include_router(karma_router.router)
	app.include_router(trust_router.router)
	app.include_router(leaderboard_router.router)
	app.include_router(verification_router.router)
	app.include_router(balances_router.router)

	return app


app = make_app()


