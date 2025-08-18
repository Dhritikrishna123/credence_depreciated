from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.orm import Session

from ...deps import AuthAdapter, get_auth_adapter, get_session_dep, get_settings
from ...schemas import DisputeOpenRequest, DisputeOut, DisputeResolveRequest
from ...services.disputes import DisputeService
from ...rate_limit import limiter

router = APIRouter(prefix="/disputes", tags=["disputes"])


@router.post("/open", response_model=DisputeOut)
@limiter.limit("30/minute")
def open_dispute(
	request: Request,
	req: DisputeOpenRequest = Body(...),
	session: Session = Depends(get_session_dep),
	auth: AuthAdapter = Depends(get_auth_adapter),
):
	try:
		service = DisputeService(session=session, settings=get_settings())
		d = service.open(ledger_entry_id=req.ledger_entry_id, opened_by=auth.get_user_id(), reason=req.reason)
		return d
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


@router.post("/resolve", response_model=DisputeOut)
@limiter.limit("30/minute")
def resolve_dispute(
	request: Request,
	req: DisputeResolveRequest = Body(...),
	session: Session = Depends(get_session_dep),
	auth: AuthAdapter = Depends(get_auth_adapter),
):
	try:
		service = DisputeService(session=session, settings=get_settings())
		d = service.resolve(dispute_id=req.dispute_id, resolved_by=auth.get_user_id(), resolution=req.resolution, note=req.note)
		return d
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


