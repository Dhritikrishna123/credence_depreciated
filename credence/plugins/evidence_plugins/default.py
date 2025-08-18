from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DefaultEvidenceValidator:
	def validate(self, evidence_ref: str | None) -> str:
		# green by default; future: implement checks or ML/CV
		return "green"


