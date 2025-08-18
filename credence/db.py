from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Generator, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from .config import Settings


class Base(DeclarativeBase):
	pass


class EvidenceStatusEnum(str, PyEnum):
	GREEN = "green"
	YELLOW = "yellow"
	RED = "red"


class LedgerEntry(Base):
	__tablename__ = "ledger_entries"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	user_id: Mapped[str] = mapped_column(String(128), index=True)
	domain: Mapped[str] = mapped_column(String(64), index=True)
	action: Mapped[str] = mapped_column(String(64))
	points: Mapped[int] = mapped_column(Integer)
	evidence_ref: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
	evidence_status: Mapped[EvidenceStatusEnum] = mapped_column(
		Enum(EvidenceStatusEnum, name="evidence_status"), default=EvidenceStatusEnum.GREEN
	)
	related_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ledger_entries.id"), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

	related_entry: Mapped[Optional["LedgerEntry"]] = relationship(remote_side=[id])


class Verification(Base):
	__tablename__ = "verifications"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	user_id: Mapped[str] = mapped_column(String(128), index=True)
	source: Mapped[str] = mapped_column(String(32))  # external | internal
	level: Mapped[int] = mapped_column(Integer, default=0)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class IdempotencyKey(Base):
	__tablename__ = "idempotency_keys"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
	user_id: Mapped[str] = mapped_column(String(128), index=True)
	domain: Mapped[str] = mapped_column(String(64))
	action: Mapped[str] = mapped_column(String(64))
	ledger_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("ledger_entries.id"), nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


def create_session_factory(settings: Settings) -> sessionmaker[Session]:
	engine = create_engine(settings.database_url, future=True)
	# Schema is managed via Alembic migrations
	return sessionmaker(bind=engine, class_=Session, expire_on_commit=False, future=True)


def get_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
	session = session_factory()
	try:
		yield session
	finally:
		session.close()


def compute_balance(session: Session, user_id: str, domain: Optional[str] = None) -> int:
	query = session.query(func.coalesce(func.sum(LedgerEntry.points), 0))
	query = query.filter(LedgerEntry.user_id == user_id)
	if domain is not None:
		query = query.filter(LedgerEntry.domain == domain)
	return int(query.scalar_one())


