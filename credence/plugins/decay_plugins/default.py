from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NoDecayPolicy:
	def apply(self, points: int, age_days: float) -> int:
		return points


