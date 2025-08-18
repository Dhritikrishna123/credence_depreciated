from __future__ import annotations

import os
from dataclasses import dataclass

from celery import Celery

from .config import Settings


def make_celery(settings: Settings | None = None) -> Celery:
	settings = settings or Settings.from_env_and_file()
	celery_app = Celery(
		"credence",
		broker=os.getenv("CELERY_BROKER_URL", settings.redis_url),
		backend=os.getenv("CELERY_RESULT_BACKEND", settings.redis_url),
	)
	return celery_app


celery_app = make_celery()


@celery_app.task(name="credence.tasks.recompute_trust")
def recompute_trust_task(user_id: str) -> str:
	# Placeholder task; real logic would compute and cache trust
	return f"recomputed:{user_id}"


