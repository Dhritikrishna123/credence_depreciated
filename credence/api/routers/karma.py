from fastapi import APIRouter, Depends, HTTPException, Header, Request, Body
from typing import Annotated
from sqlalchemy.orm import Session

from ...deps import AuthAdapter, get_auth_adapter, get_session_dep, get_settings
from ...schemas import AwardRequest, FlagEvidenceRequest, LedgerEntryOut, ReverseRequest, FlagEvidenceResponse
from ...services.karma import KarmaService
from ...rate_limit import limiter

router = APIRouter(prefix="/karma", tags=["karma"])


@router.post("/award", response_model=LedgerEntryOut)
@limiter.limit("120/minute")
def award(
	request: Request,
	req: Annotated[AwardRequest, Body(...)],
	session: Session = Depends(get_session_dep),
	auth: AuthAdapter = Depends(get_auth_adapter),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
	"""Award karma points to the authenticated user.

	Args:
		req: Payload containing `domain`, `action`, optional `evidence_ref` and `meta`.
		session: Database session (injected).
		auth: Auth adapter to resolve current user id.
		idempotency_key: Optional header `Idempotency-Key` to safely retry requests.

	Returns:
		The created ledger entry.

	Raises:
		HTTPException: on validation errors, permission errors, or limits exceeded.
	"""
	try:
		service = KarmaService(session=session, settings=get_settings())
		entry = service.award(
			user_id=auth.get_user_id(),
			domain=req.domain,
			action=req.action,
			evidence_ref=req.evidence_ref,
			idempotency_key=idempotency_key,
			meta=req.meta,
		)
		return entry
	except (ValueError, PermissionError) as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.post("/reverse", response_model=LedgerEntryOut)
@limiter.limit("60/minute")
def reverse(
	request: Request,
	req: Annotated[ReverseRequest, Body(...)],
	session: Session = Depends(get_session_dep),
	auth: AuthAdapter = Depends(get_auth_adapter),
):
	"""Append a reversing entry for an existing ledger entry belonging to the caller.

	Args:
		req: Body with `entry_id` of the original ledger entry.

	Returns:
		The reversal ledger entry.
	"""
	try:
		service = KarmaService(session=session, settings=get_settings())
		entry = service.reverse(user_id=auth.get_user_id(), original_entry_id=req.entry_id)
		return entry
	except (ValueError, PermissionError) as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.post("/flag", response_model=FlagEvidenceResponse)
@limiter.limit("60/minute")
def flag(
	request: Request,
	req: Annotated[FlagEvidenceRequest, Body(...)],
	session: Session = Depends(get_session_dep),
):
	"""Record an append-only evidence flag (yellow/red) for a ledger entry.

	Args:
		req: Body with `entry_id` and `status` (yellow|red).

	Returns:
		A record describing the evidence flag event.
	"""
	try:
		service = KarmaService(session=session, settings=get_settings())
		flag = service.flag_evidence(entry_id=req.entry_id, status=req.status)
		return FlagEvidenceResponse(id=flag.id, ledger_entry_id=flag.ledger_entry_id, status=flag.status, created_at=flag.created_at)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


