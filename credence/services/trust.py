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
		# Compute external vs internal maxima then combine via provider
		external_level = int(
			self.session.query(func.coalesce(func.max(Verification.level), 0))
			.filter(Verification.user_id == user_id, Verification.source == "external")
			.scalar_one()
		)
		internal_level = int(
			self.session.query(func.coalesce(func.max(Verification.level), 0))
			.filter(Verification.user_id == user_id, Verification.source == "internal")
			.scalar_one()
		)
		provider_cls = load_symbol(self.settings.plugins.verification_provider)
		provider = provider_cls()  # type: ignore[call-arg]
		return int(provider.effective_level(external_level, internal_level))

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


