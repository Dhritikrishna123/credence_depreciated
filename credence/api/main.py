from __future__ import annotations

from fastapi import Depends, FastAPI

from ..config import Settings
from ..db import create_session_factory, get_session


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
	@app.get("/balance/{user_id}")
	def balance(user_id: str, settings: Settings = Depends(get_settings)) -> dict[str, str | int]:
		# Placeholder endpoint for now; real logic will be added in services/routers
		return {"user_id": user_id, "database": settings.database_url}

	return app


app = make_app()


