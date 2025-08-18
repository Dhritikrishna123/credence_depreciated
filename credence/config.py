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
				return cls(**file_settings)
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


