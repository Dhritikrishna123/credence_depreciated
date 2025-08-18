from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...deps import get_session_dep, get_settings
from ...schemas import TrustResponse
from ...services.trust import TrustService

router = APIRouter(prefix="/trust", tags=["trust"])


@router.get("/{user_id}", response_model=TrustResponse)
def get_trust(user_id: str, session: Session = Depends(get_session_dep)) -> TrustResponse:
	service = TrustService(session=session, settings=get_settings())
	trust, balance, verification = service.compute_trust(user_id)
	return TrustResponse(user_id=user_id, trust=trust, karma_balance=balance, verification_level=verification)


