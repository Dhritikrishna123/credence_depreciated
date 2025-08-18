from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import redis

from .config import Settings


@dataclass
class RedisCache:
	client: redis.Redis

	@classmethod
	def from_settings(cls, settings: Settings) -> "RedisCache":
		client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
		return cls(client=client)

	def get(self, key: str) -> Optional[str]:
		value = self.client.get(key)
		return value if value is not None else None

	def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
		if ttl_seconds is not None:
			self.client.setex(key, ttl_seconds, value)
		else:
			self.client.set(key, value)

	def delete(self, *keys: str) -> None:
		if keys:
			self.client.delete(*keys)


def balance_cache_key(user_id: str, domain: str | None) -> str:
	return f"balance:{user_id}:{domain or '_all'}"


