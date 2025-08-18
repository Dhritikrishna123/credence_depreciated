from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ...deps import get_session_dep, get_settings
from ...schemas import TrustResponse
from ...services.trust import TrustService
from ...cache import RedisCache, trust_cache_key
from ...worker import recompute_trust_task

router = APIRouter(prefix="/trust", tags=["trust"])


@router.get("/{user_id}", response_model=TrustResponse)
def get_trust(user_id: str, domain: str | None = None, session: Session = Depends(get_session_dep)) -> TrustResponse:
	"""Get the user's trust score, balance, and verification level.

	Tries Redis cache first; on cache miss, computes via plugin formula,
	caches the result briefly, and enqueues background persistence.

	Args:
		user_id: Subject user id.
		domain: Optional domain to scope trust (defaults to all).

	Returns:
		TrustResponse with trust, karma_balance, and verification_level.
	"""
	settings = get_settings()
	cache = RedisCache.from_settings(settings)
	ck = trust_cache_key(user_id, domain)
	cached = cache.get(ck)
	if cached is not None:
		try:
			trust_value = float(cached)
			service = TrustService(session=session, settings=settings)
			# Still compute balance and verification for full response
			trust_calc, balance, verification = service.compute_trust(user_id, domain)
			return TrustResponse(user_id=user_id, trust=trust_value, karma_balance=balance, verification_level=verification)
		except ValueError:
			pass

	service = TrustService(session=session, settings=settings)
	trust, balance, verification = service.compute_trust(user_id, domain)
	cache.set(ck, str(trust), ttl_seconds=60)
	# Enqueue persistence via worker
	recompute_trust_task.delay(user_id, domain)
	return TrustResponse(user_id=user_id, trust=trust, karma_balance=balance, verification_level=verification)


