from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...deps import get_session_dep
from ...schemas import VerificationSetRequest
from ...services.verification import VerificationService

router = APIRouter(prefix="/verification", tags=["verification"])


@router.post("/set")
def set_verification(req: VerificationSetRequest, session: Session = Depends(get_session_dep)):
	try:
		service = VerificationService(session=session)
		v = service.set_level(user_id=req.user_id, source=req.source, level=req.level)
		return {"id": v.id, "user_id": v.user_id, "source": v.source, "level": v.level}
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


