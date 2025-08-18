from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Tuple

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ...deps import get_session_dep, get_settings
from ...db import LedgerEntry
from ...plugins import load_symbol
from ...schemas import LeaderboardItem, LeaderboardResponse

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/")
def leaderboard(
	domain: str | None = None,
	since_days: int | None = None,
	session: Session = Depends(get_session_dep),
):
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
	items_sorted = strategy.rank(rows)

	return LeaderboardResponse(
		domain=domain,
		since_days=since_days,
		items=[LeaderboardItem(user_id=u, points=p) for u, p in items_sorted],
	)


