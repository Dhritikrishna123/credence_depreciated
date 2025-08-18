from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...deps import AuthAdapter, get_auth_adapter, get_session_dep, get_settings
from ...schemas import AwardRequest, FlagEvidenceRequest, LedgerEntryOut, ReverseRequest
from ...services.karma import KarmaService
from ...rate_limit import limiter

router = APIRouter(prefix="/karma", tags=["karma"])


@router.post("/award", response_model=LedgerEntryOut)
@limiter.limit("120/minute")
def award(
	req: AwardRequest,
	session: Session = Depends(get_session_dep),
	auth: AuthAdapter = Depends(get_auth_adapter),
    idempotency_key: str | None = None,
):
	try:
		service = KarmaService(session=session, settings=get_settings())
		entry = service.award(
			user_id=auth.get_user_id(),
			domain=req.domain,
			action=req.action,
			evidence_ref=req.evidence_ref,
			idempotency_key=idempotency_key,
		)
		return entry
	except (ValueError, PermissionError) as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.post("/reverse", response_model=LedgerEntryOut)
@limiter.limit("60/minute")
def reverse(
	req: ReverseRequest,
	session: Session = Depends(get_session_dep),
	auth: AuthAdapter = Depends(get_auth_adapter),
):
	try:
		service = KarmaService(session=session, settings=get_settings())
		entry = service.reverse(user_id=auth.get_user_id(), original_entry_id=req.entry_id)
		return entry
	except (ValueError, PermissionError) as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.post("/flag", response_model=LedgerEntryOut)
@limiter.limit("60/minute")
def flag(
	req: FlagEvidenceRequest,
	session: Session = Depends(get_session_dep),
):
	try:
		service = KarmaService(session=session, settings=get_settings())
		entry = service.flag_evidence(entry_id=req.entry_id, status=req.status)
		return entry
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


