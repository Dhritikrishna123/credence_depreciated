from __future__ import annotations

import os
from dataclasses import dataclass

from celery import Celery

from .config import Settings
from .cache import RedisCache, trust_cache_key
from .db import LedgerEntry, Verification, TrustScore
from .plugins import load_symbol
from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker


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
def recompute_trust_task(user_id: str, domain: str | None = None) -> str:
	settings = Settings.from_env_and_file()
	# Build a session factory locally to avoid global coupling
	from .db import create_session_factory
	session_factory: sessionmaker[Session] = create_session_factory(settings)
	session = session_factory()
	try:
		# Compute balance
		q = session.query(func.coalesce(func.sum(LedgerEntry.points), 0)).filter(LedgerEntry.user_id == user_id)
		if domain is not None:
			q = q.filter(LedgerEntry.domain == domain)
		balance = int(q.scalar_one())

		# Verification level (max of external/internal via provider)
		external_level = int(
			session.query(func.coalesce(func.max(Verification.level), 0))
			.filter(Verification.user_id == user_id, Verification.source == "external")
			.scalar_one()
		)
		internal_level = int(
			session.query(func.coalesce(func.max(Verification.level), 0))
			.filter(Verification.user_id == user_id, Verification.source == "internal")
			.scalar_one()
		)
		provider_cls = load_symbol(settings.plugins.verification_provider)
		provider = provider_cls()  # type: ignore[call-arg]
		verif_level = int(provider.effective_level(external_level, internal_level))

		# Trust formula
		formula_cls = load_symbol(settings.plugins.trust_formula)
		formula = formula_cls()  # type: ignore[call-arg]
		trust_value = float(formula.compute(balance, verif_level))

		# Persist snapshot
		rec = TrustScore(
			user_id=user_id,
			domain=domain,
			trust=trust_value,
			karma_balance=balance,
			verification_level=verif_level,
		)
		session.add(rec)
		session.commit()

		# Cache current trust
		cache = RedisCache.from_settings(settings)
		cache.set(trust_cache_key(user_id, domain), str(trust_value), ttl_seconds=60)
		return f"trust:{user_id}:{domain or '_all'}={trust_value}"
	finally:
		session.close()


@celery_app.task(name="credence.tasks.apply_decay")
def apply_decay_task() -> str:
	"""Periodically apply decay policies and persist new ledger entries representing decay."""
	settings = Settings.from_env_and_file()
	from .db import create_session_factory
	session_factory: sessionmaker[Session] = create_session_factory(settings)
	session = session_factory()
	try:
		# Load decay policy plugin
		policy_cls = load_symbol(settings.plugins.decay_policy)
		policy = policy_cls()  # type: ignore[call-arg]
		# For simplicity: no-op placeholder for now
		# Future: iterate users/domains, compute age_days on entries, write compensating entries
		return "decay:ok"
	finally:
		session.close()


