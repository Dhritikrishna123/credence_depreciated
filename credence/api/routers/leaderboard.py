from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ...deps import get_session_dep, get_settings
from ...db import LedgerEntry, TrustScore
from ...plugins import load_symbol
from ...schemas import LeaderboardItem, LeaderboardResponse

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/")
def leaderboard(
	domain: str | None = None,
	since_days: int | None = None,
	mode: str | None = None,
	session: Session = Depends(get_session_dep),
):
	"""Return leaderboard items.

	Args:
		domain: Optional domain filter.
		since_days: Restrict to points gained within the last N days.
		mode: Ranking mode: None (sum of points), 'trust_weighted', or 'recency_weighted'.

	Returns:
		LeaderboardResponse containing ranked items.
	"""
	settings = get_settings()
	strategy_cls = load_symbol(settings.plugins.leaderboard_strategy)
	strategy = strategy_cls()  # type: ignore[call-arg]

	q = session.query(LedgerEntry.user_id, func.coalesce(func.sum(LedgerEntry.points), 0))
	if domain is not None:
		q = q.filter(LedgerEntry.domain == domain)
	if since_days is not None:
		start = datetime.now(timezone.utc) - timedelta(days=since_days)
		q = q.filter(LedgerEntry.created_at >= start)
	q = q.group_by(LedgerEntry.user_id)

	rows: List[Tuple[str, int]] = [(user_id, int(total)) for user_id, total in q.all()]

	if mode == "trust_weighted":
		trust_by_user = {
			user_id: float(
				session.query(func.coalesce(func.max(TrustScore.trust), 0.0))
				.filter(TrustScore.user_id == user_id)
				.scalar() or 0.0
			)
			for user_id, _ in rows
		}
		weighted: List[Tuple[str, int]] = []
		for user_id, pts in rows:
			trust = trust_by_user.get(user_id, 0.0)
			weighted.append((user_id, int(round(pts * (1.0 + trust)))))
		items_sorted = strategy.rank(weighted)
	elif mode == "recency_weighted":
		# Weight by last 7d points added to total
		start_recent = datetime.now(timezone.utc) - timedelta(days=7)
		q_recent = session.query(LedgerEntry.user_id, func.coalesce(func.sum(LedgerEntry.points), 0))
		if domain is not None:
			q_recent = q_recent.filter(LedgerEntry.domain == domain)
		q_recent = q_recent.filter(LedgerEntry.created_at >= start_recent).group_by(LedgerEntry.user_id)
		recent_map = {u: int(p) for u, p in q_recent.all()}
		weighted = []
		for user_id, pts in rows:
			weighted.append((user_id, pts + recent_map.get(user_id, 0)))
		items_sorted = strategy.rank(weighted)
	else:
		items_sorted = strategy.rank(rows)

	return LeaderboardResponse(
		domain=domain,
		since_days=since_days,
		items=[LeaderboardItem(user_id=u, points=p) for u, p in items_sorted],
	)


