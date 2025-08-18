from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException


@dataclass
class NoAuthProvider:
	def get_user_id(self, x_user_id: Optional[str] = Header(default=None)) -> str:
		if not x_user_id:
			raise HTTPException(status_code=401, detail="Missing X-User-Id header in NoAuth mode")
		return x_user_id


