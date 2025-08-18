from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..config import Settings
from ..db import LedgerEntry, Verification
from ..plugins import load_symbol


@dataclass
class TrustService:
	session: Session
	settings: Settings

	def get_verification_level(self, user_id: str) -> int:
		levels = (
			self.session.query(func.coalesce(func.max(Verification.level), 0))
			.filter(Verification.user_id == user_id)
			.scalar_one()
		)
		return int(levels)

	def compute_trust(self, user_id: str, domain: Optional[str] = None) -> tuple[float, int, int]:
		# balance
		q = self.session.query(func.coalesce(func.sum(LedgerEntry.points), 0)).filter(
			LedgerEntry.user_id == user_id
		)
		if domain is not None:
			q = q.filter(LedgerEntry.domain == domain)
		balance = int(q.scalar_one())

		verification_level = self.get_verification_level(user_id)
		formula_cls = load_symbol(self.settings.plugins.trust_formula)
		formula = formula_cls()  # type: ignore[call-arg]
		trust = float(formula.compute(balance, verification_level))
		return trust, balance, verification_level


