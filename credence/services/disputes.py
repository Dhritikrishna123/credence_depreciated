from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..db import Dispute, DisputeStatusEnum, LedgerEntry
from ..config import Settings
from . import WebhookClient
from . import WebhookClient


@dataclass
class DisputeService:
	session: Session
	settings: Settings

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
		WebhookClient(settings=self.settings).send_event(
			"dispute.opened",
			{
				"id": d.id,
				"ledger_entry_id": d.ledger_entry_id,
				"opened_by": d.opened_by,
				"reason": d.reason,
				"created_at": d.created_at.isoformat(),
			},
		)
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
		WebhookClient(settings=self.settings).send_event(
			"dispute.resolved",
			{
				"id": d.id,
				"status": d.status,
				"resolved_by": d.resolved_by,
				"resolved_at": d.resolved_at.isoformat() if d.resolved_at else None,
			},
		)
		return d


