from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..db import Verification


@dataclass
class VerificationService:
	session: Session

	"""Manage verification level records for users."""

	def set_level(self, user_id: str, source: str, level: int) -> Verification:
		"""Insert a verification record with a source (external|internal)."""
		if source not in {"external", "internal"}:
			raise ValueError("source must be 'external' or 'internal'")
		verification = Verification(user_id=user_id, source=source, level=level)
		self.session.add(verification)
		self.session.commit()
		self.session.refresh(verification)
		return verification


