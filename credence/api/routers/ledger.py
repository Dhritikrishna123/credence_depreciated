from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...deps import get_session_dep
from ...db import LedgerEntry
from ...schemas import LedgerEntryOut, LedgerPageResponse


router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("/{user_id}", response_model=LedgerPageResponse)
def list_ledger(
	user_id: str,
	domain: str | None = None,
	page: int = 1,
	page_size: int = 50,
	session: Session = Depends(get_session_dep),
):
	"""Paginated ledger history for a user, newest first.

	Args:
		user_id: Subject user id.
		domain: Optional domain filter.
		page: 1-based page index.
		page_size: Items per page (max 200).
	"""
	page = max(1, page)
	page_size = min(max(1, page_size), 200)
	q = session.query(LedgerEntry).filter(LedgerEntry.user_id == user_id)
	if domain is not None:
		q = q.filter(LedgerEntry.domain == domain)
	total = q.count()
	items = (
		q.order_by(LedgerEntry.created_at.desc())
		.offset((page - 1) * page_size)
		.limit(page_size)
		.all()
	)
	return LedgerPageResponse(
		user_id=user_id,
		domain=domain,
		page=page,
		page_size=page_size,
		total=total,
		items=[LedgerEntryOut.model_validate(i) for i in items],
	)


@router.get("/export")
def export_ledger(
	user_id: str | None = None,
	domain: str | None = None,
	format: str = "json",
	session: Session = Depends(get_session_dep),
):
	"""Export ledger data as JSON or CSV.

	Args:
		user_id: Optional user filter.
		domain: Optional domain filter.
		format: 'json' or 'csv'.
	"""
	q = session.query(LedgerEntry)
	if user_id is not None:
		q = q.filter(LedgerEntry.user_id == user_id)
	if domain is not None:
		q = q.filter(LedgerEntry.domain == domain)
	rows = q.order_by(LedgerEntry.created_at.desc()).all()
	if format == "csv":
		import io
		import csv
		buf = io.StringIO()
		writer = csv.writer(buf)
		writer.writerow(["id", "user_id", "domain", "action", "points", "evidence_ref", "evidence_status", "related_entry_id", "created_at"])
		for r in rows:
			writer.writerow([
				r.id,
				r.user_id,
				r.domain,
				r.action,
				r.points,
				r.evidence_ref or "",
				r.evidence_status,
				r.related_entry_id or "",
				r.created_at.isoformat(),
			])
		return {"format": "csv", "data": buf.getvalue()}
	# default json
	return [LedgerEntryOut.model_validate(r).model_dump() for r in rows]


