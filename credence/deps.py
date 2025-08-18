from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generator

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings
from .db import get_session
from .plugins import load_symbol


def get_settings() -> Settings:
	return Settings.from_env_and_file()


def get_session_dep(
	session_factory: sessionmaker[Session] = Depends(
		lambda settings=Depends(get_settings): __get_session_factory(settings)
	)
) -> Generator[Session, None, None]:
	yield from get_session(session_factory)


def __get_session_factory(settings: Settings) -> sessionmaker[Session]:
	from .db import create_session_factory

	return create_session_factory(settings)


@dataclass
class AuthAdapter:
	get_user_id: Callable[..., str]


def get_auth_adapter(settings: Settings = Depends(get_settings)) -> AuthAdapter:
	provider_cls = load_symbol(settings.plugins.auth_provider)
	provider = provider_cls()  # type: ignore[call-arg]
	return AuthAdapter(get_user_id=provider.get_user_id)


