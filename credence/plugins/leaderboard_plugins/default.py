from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple


@dataclass
class DefaultLeaderboardStrategy:
	def rank(self, user_points: Iterable[Tuple[str, int]]) -> List[Tuple[str, int]]:
		return sorted(user_points, key=lambda x: x[1], reverse=True)


