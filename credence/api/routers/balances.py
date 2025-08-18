from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...cache import RedisCache, balance_cache_key
from ...deps import get_session_dep, get_settings
from ...db import compute_balance
from ...schemas import BalanceResponse

router = APIRouter(prefix="/balances", tags=["balances"])


@router.get("/{user_id}", response_model=BalanceResponse)
def get_balance(user_id: str, domain: str | None = None, session: Session = Depends(get_session_dep)) -> BalanceResponse:
	"""Get a user's karma balance, optionally scoped to a domain.

	Uses Redis cache with a short TTL; invalidated when new entries are added.

	Args:
		user_id: Subject user id.
		domain: Optional domain.

	Returns:
		BalanceResponse with the current balance.
	"""
	settings = get_settings()
	cache = RedisCache.from_settings(settings)
	ck = balance_cache_key(user_id, domain)
	cached = cache.get(ck)
	if cached is not None:
		try:
			value = int(cached)
			return BalanceResponse(user_id=user_id, domain=domain, balance=value)
		except ValueError:
			pass

	value = compute_balance(session, user_id, domain)
	# cache for 15s to avoid thrash, invalidate on new ledger writes in service
	cache.set(ck, str(value), ttl_seconds=15)
	return BalanceResponse(user_id=user_id, domain=domain, balance=value)


