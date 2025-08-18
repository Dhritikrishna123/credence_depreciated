from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class DefaultEvidenceValidator:
	def validate(self, evidence_ref: str | None) -> str:
		# Simple heuristic: missing -> yellow if required; explicit "flag:" prefix -> red, "warn:" -> yellow
		if evidence_ref is None or evidence_ref.strip() == "":
			return "yellow"
		lower = evidence_ref.lower()
		if lower.startswith("flag:"):
			return "red"
		if lower.startswith("warn:"):
			return "yellow"
		return "green"


