from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...deps import get_session_dep
from ...db import LedgerEntry, Dispute, Verification


router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/")
def get_stats(session: Session = Depends(get_session_dep)):
	users = session.query(func.count(func.distinct(LedgerEntry.user_id))).scalar() or 0
	disputes_open = session.query(func.count(Dispute.id)).filter(Dispute.status == 'open').scalar() or 0
	total_entries = session.query(func.count(LedgerEntry.id)).scalar() or 0
	pos = session.query(func.coalesce(func.sum(func.case((LedgerEntry.points > 0, LedgerEntry.points), else_=0))),).scalar() or 0
	neg = session.query(func.coalesce(func.sum(func.case((LedgerEntry.points < 0, LedgerEntry.points), else_=0))),).scalar() or 0
	verified_users = session.query(func.count(func.distinct(Verification.user_id))).filter(Verification.level > 0).scalar() or 0
	return {
		"total_users": int(users),
		"verified_users": int(verified_users),
		"disputes_open": int(disputes_open),
		"ledger_entries": int(total_entries),
		"karma_positive_sum": int(pos),
		"karma_negative_sum": int(neg),
	}


