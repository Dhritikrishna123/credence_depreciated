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
		"""Create a Redis client from configuration."""
		client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
		return cls(client=client)

	def get(self, key: str) -> Optional[str]:
		"""Get a string value or None if missing."""
		value = self.client.get(key)
		return value if value is not None else None

	def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
		"""Set a string value with optional TTL in seconds."""
		if ttl_seconds is not None:
			self.client.setex(key, ttl_seconds, value)
		else:
			self.client.set(key, value)

	def delete(self, *keys: str) -> None:
		"""Delete one or more keys if they exist."""
		if keys:
			self.client.delete(*keys)


def balance_cache_key(user_id: str, domain: str | None) -> str:
	"""Cache key for balances."""
	return f"balance:{user_id}:{domain or '_all'}"


def trust_cache_key(user_id: str, domain: str | None = None) -> str:
	"""Cache key for trust values."""
	return f"trust:{user_id}:{domain or '_all'}"


