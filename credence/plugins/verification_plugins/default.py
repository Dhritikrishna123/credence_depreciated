from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DefaultVerificationProvider:
	def effective_level(self, external_level: int, internal_level: int) -> int:
		return max(external_level, internal_level)


