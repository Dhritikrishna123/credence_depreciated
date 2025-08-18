from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from fastapi import Header, HTTPException
from jose import jwt

from ..config import Settings


@dataclass
class JWKSCache:
	url: str
	_ttl_seconds: int = 300
	_cached: Optional[Dict[str, Any]] = None
	_cached_at: float = 0.0

	def get(self) -> Dict[str, Any]:
		now = time.time()
		if self._cached and now - self._cached_at < self._ttl_seconds:
			return self._cached
		resp = requests.get(self.url, timeout=5)
		resp.raise_for_status()
		self._cached = resp.json()
		self._cached_at = now
		return self._cached


@dataclass
class JwtAuthProvider:
	settings: Settings
	jwks_cache: JWKSCache

	@classmethod
	def from_settings(cls, settings: Settings) -> "JwtAuthProvider":
		if not settings.jwks_url:
			raise RuntimeError("jwks_url is required for JwtAuthProvider")
		return cls(settings=settings, jwks_cache=JWKSCache(url=settings.jwks_url))

	def get_user_id(self, authorization: Optional[str] = Header(default=None)) -> str:
		if not authorization or not authorization.lower().startswith("bearer "):
			raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
		token = authorization.split(" ", 1)[1]
		jwks = self.jwks_cache.get()
		try:
			claims = jwt.decode(
				token,
				jwks,  # jose accepts JWKS dict
				options={"verify_aud": bool(self.settings.jwt_audience)},
				audience=self.settings.jwt_audience,
				issuer=self.settings.jwt_issuer,
			)
		except Exception as exc:  # jose.JWSError and friends
			raise HTTPException(status_code=401, detail=f"JWT verification failed: {exc}")
		user_id = str(claims.get("sub"))
		if not user_id:
			raise HTTPException(status_code=401, detail="JWT missing sub claim")
		return user_id


