from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PluginConfig(BaseModel):
	trust_formula: str = Field(
		default="credence.plugins.trust.formulas.default:DefaultTrustFormula"
	)
	evidence_validator: str = Field(
		default="credence.plugins.evidence_plugins.default:DefaultEvidenceValidator"
	)
	verification_provider: str = Field(
		default="credence.plugins.verification_plugins.default:DefaultVerificationProvider"
	)
	decay_policy: str = Field(
		default="credence.plugins.decay_plugins.default:NoDecayPolicy"
	)
	leaderboard_strategy: str = Field(
		default="credence.plugins.leaderboard_plugins.default:DefaultLeaderboardStrategy"
	)
	auth_provider: str = Field(
		default="credence.auth_providers.no_auth:NoAuthProvider"
	)


class DomainActionConfig(BaseModel):
	points: int = 0
	max_per_day: Optional[int] = None
	requires_evidence: bool = False


class Settings(BaseSettings):
	model_config = SettingsConfigDict(env_prefix="CREDENCE_", extra="ignore")

	app_name: str = "credence"
	database_url: str = Field(default_factory=lambda: "postgresql+psycopg://credence:credence@localhost:5432/credence")
	config_path: Optional[str] = None
	redis_url: str = Field(default_factory=lambda: "redis://localhost:6379/0")
	# Webhooks
	webhook_url: Optional[str] = None
	webhook_secret: Optional[str] = None
	webhook_timeout_seconds: int = Field(default=5)
	# JWT config (for JwtAuthProvider)
	jwks_url: Optional[str] = None
	jwt_issuer: Optional[str] = None
	jwt_audience: Optional[str] = None
	# Rate limiting
	rate_limit_default: str = Field(default="60/minute")
	plugins: PluginConfig = Field(default_factory=PluginConfig)
	# domain -> action -> config
	domains: Dict[str, Dict[str, DomainActionConfig]] = Field(default_factory=dict)

	@classmethod
	def from_env_and_file(cls) -> "Settings":
		base = cls()
		path = base.config_path or _env_config_path()
		if path:
			file_settings = _load_yaml(path)
			if file_settings:
				_validate_config_schema(file_settings)
				# Merge with precedence: environment (base) overrides YAML
				merged: Dict[str, Any] = {**file_settings, **{k: v for k, v in base.model_dump().items() if v is not None}}
				return cls(**merged)
		return base


def _env_config_path() -> Optional[str]:
	# pydantic-settings already handles env vars for Settings; here we only look for a YAML file path
	from os import getenv

	return getenv("CREDENCE_CONFIG")


def _load_yaml(path_str: str) -> Optional[Mapping[str, Any]]:
	path = Path(path_str)
	if not path.exists():
		return None
	with path.open("r", encoding="utf-8") as f:
		data = yaml.safe_load(f) or {}
	if not isinstance(data, dict):
		return None
	return data


def _validate_config_schema(data: Mapping[str, Any]) -> None:
	"""Basic JSONSchema-like validation for known fields.

	Intentionally minimal to avoid a hard dependency; ensures types for top-level
	keys we rely on. Extend as config evolves.
	"""
	if not isinstance(data, Mapping):
		raise ValueError("config must be a mapping")
	plugins = data.get("plugins")
	if plugins is not None and not isinstance(plugins, Mapping):
		raise ValueError("plugins must be a mapping")
	domains = data.get("domains")
	if domains is not None and not isinstance(domains, Mapping):
		raise ValueError("domains must be a mapping")
	# spot-check domain/action shapes
	if isinstance(domains, Mapping):
		for domain_name, actions in domains.items():
			if not isinstance(actions, Mapping):
				raise ValueError(f"domain '{domain_name}' must map to action configs")
			for action_name, cfg in actions.items():
				if not isinstance(cfg, Mapping):
					raise ValueError(f"action '{domain_name}.{action_name}' must be a mapping")
				if "points" in cfg and not isinstance(cfg["points"], int):
					raise ValueError(f"action '{domain_name}.{action_name}.points' must be int")
				if "max_per_day" in cfg and cfg["max_per_day"] is not None and not isinstance(cfg["max_per_day"], int):
					raise ValueError(f"action '{domain_name}.{action_name}.max_per_day' must be int or null")
				if "requires_evidence" in cfg and not isinstance(cfg["requires_evidence"], bool):
					raise ValueError(f"action '{domain_name}.{action_name}.requires_evidence' must be bool")


