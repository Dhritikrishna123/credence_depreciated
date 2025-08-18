from __future__ import annotations

from typing import Iterable, List, Protocol, Tuple


class TrustFormula(Protocol):
	def compute(self, karma_balance: int, verification_level: int) -> float: ...


class EvidenceValidator(Protocol):
	def validate(self, evidence_ref: str | None) -> str: ...


class VerificationProvider(Protocol):
	def effective_level(self, external_level: int, internal_level: int) -> int: ...


class DecayPolicy(Protocol):
	def apply(self, points: int, age_days: float) -> int: ...


class LeaderboardStrategy(Protocol):
	def rank(self, user_points: Iterable[Tuple[str, int]]) -> List[Tuple[str, int]]: ...


class AuthProvider(Protocol):
	def get_user_id(self, *args, **kwargs) -> str: ...


