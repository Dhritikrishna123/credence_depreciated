from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DefaultTrustFormula:
	base: float = 0.0
	multiplier: float = 0.1

	def compute(self, karma_balance: int, verification_level: int) -> float:
		trust = self.base + self.multiplier * float(karma_balance) + 0.5 * float(verification_level)
		return max(0.0, trust)


