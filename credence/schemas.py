from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AwardRequest(BaseModel):
	domain: str
	action: str
	evidence_ref: Optional[str] = None


class LedgerEntryOut(BaseModel):
	id: int
	user_id: str
	domain: str
	action: str
	points: int
	evidence_ref: Optional[str]
	evidence_status: str
	related_entry_id: Optional[int]
	created_at: datetime

	class Config:
		from_attributes = True


class BalanceResponse(BaseModel):
	user_id: str
	domain: Optional[str] = None
	balance: int


class ReverseRequest(BaseModel):
	entry_id: int = Field(..., description="Original ledger entry id to reverse")


class FlagEvidenceRequest(BaseModel):
	entry_id: int
	status: str = Field(..., pattern="^(yellow|red)$")


class VerificationSetRequest(BaseModel):
	user_id: str
	source: str  # external | internal
	level: int = Field(ge=0)


class TrustResponse(BaseModel):
	user_id: str
	trust: float
	karma_balance: int
	verification_level: int


class LeaderboardItem(BaseModel):
	user_id: str
	points: int


class LeaderboardResponse(BaseModel):
	domain: Optional[str] = None
	since_days: Optional[int] = None
	items: list[LeaderboardItem]


class DisputeOpenRequest(BaseModel):
	ledger_entry_id: int
	reason: str


class DisputeResolveRequest(BaseModel):
	dispute_id: int
	resolution: str  # resolved | rejected
	note: Optional[str] = None


class DisputeOut(BaseModel):
	id: int
	ledger_entry_id: int
	opened_by: str
	reason: str
	status: str
	resolution_note: Optional[str]
	resolved_by: Optional[str]
	resolved_at: Optional[datetime]
	created_at: datetime

	class Config:
		from_attributes = True


