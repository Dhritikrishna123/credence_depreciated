from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..db import Dispute, DisputeStatusEnum, LedgerEntry


@dataclass
class DisputeService:
	session: Session

	def open(self, ledger_entry_id: int, opened_by: str, reason: str) -> Dispute:
		entry = self.session.get(LedgerEntry, ledger_entry_id)
		if entry is None:
			raise ValueError("Ledger entry not found")
		d = Dispute(
			ledger_entry_id=ledger_entry_id,
			opened_by=opened_by,
			reason=reason,
			status=DisputeStatusEnum.OPEN,
		)
		self.session.add(d)
		self.session.commit()
		self.session.refresh(d)
		return d

	def resolve(self, dispute_id: int, resolved_by: str, resolution: str, note: str | None) -> Dispute:
		d = self.session.get(Dispute, dispute_id)
		if d is None:
			raise ValueError("Dispute not found")
		if resolution not in {DisputeStatusEnum.RESOLVED.value, DisputeStatusEnum.REJECTED.value}:
			raise ValueError("Invalid resolution")
		d.status = DisputeStatusEnum(resolution)
		d.resolution_note = note
		d.resolved_by = resolved_by
		d.resolved_at = datetime.now(timezone.utc)
		self.session.commit()
		self.session.refresh(d)
		return d


