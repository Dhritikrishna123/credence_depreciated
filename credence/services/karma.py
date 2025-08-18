from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..config import DomainActionConfig, Settings
from ..db import EvidenceStatusEnum, IdempotencyKey, LedgerEntry
from ..plugins import load_symbol
from ..cache import RedisCache, balance_cache_key


@dataclass
class KarmaService:
	session: Session
	settings: Settings

	def _get_action_config(self, domain: str, action: str) -> DomainActionConfig:
		try:
			return self.settings.domains[domain][action]
		except KeyError:
			raise ValueError(f"Unknown domain/action: {domain}/{action}")

	def award(self, user_id: str, domain: str, action: str, evidence_ref: Optional[str], idempotency_key: Optional[str] = None) -> LedgerEntry:
		cfg = self._get_action_config(domain, action)
		if cfg.requires_evidence and not evidence_ref:
			raise ValueError("Evidence is required for this action")

		validator_cls = load_symbol(self.settings.plugins.evidence_validator)
		validator = validator_cls()  # type: ignore[call-arg]
		evidence_status = validator.validate(evidence_ref)

		if cfg.max_per_day is not None:
			start = datetime.now(timezone.utc) - timedelta(days=1)
			count_q = (
				self.session.query(func.count(LedgerEntry.id))
				.filter(
					and_(
						LedgerEntry.user_id == user_id,
						LedgerEntry.domain == domain,
						LedgerEntry.action == action,
						LedgerEntry.created_at >= start,
					)
				)
			)
			if int(count_q.scalar_one()) >= cfg.max_per_day:
				raise ValueError("Daily limit reached for this action")

		# idempotency
		if idempotency_key:
			existing = (
				self.session.query(IdempotencyKey)
				.filter(IdempotencyKey.key == idempotency_key)
				.one_or_none()
			)
			if existing and existing.ledger_entry_id:
				entry_existing = self.session.get(LedgerEntry, existing.ledger_entry_id)
				if entry_existing:
					return entry_existing

		entry = LedgerEntry(
			user_id=user_id,
			domain=domain,
			action=action,
			points=cfg.points,
			evidence_ref=evidence_ref,
			evidence_status=evidence_status,
		)
		self.session.add(entry)
		self.session.commit()
		self.session.refresh(entry)

		# upsert idempotency key -> ledger id
		if idempotency_key:
			idem = IdempotencyKey(
				key=idempotency_key,
				user_id=user_id,
				domain=domain,
				action=action,
				ledger_entry_id=entry.id,
			)
			self.session.add(idem)
			self.session.commit()

		# invalidate cached balances
		cache = RedisCache.from_settings(self.settings)
		cache.delete(
			balance_cache_key(user_id, None),
			balance_cache_key(user_id, domain),
		)
		return entry

	def reverse(self, user_id: str, original_entry_id: int) -> LedgerEntry:
		orig = self.session.get(LedgerEntry, original_entry_id)
		if orig is None:
			raise ValueError("Original entry not found")
		if orig.user_id != user_id:
			raise PermissionError("Cannot reverse another user's entry")

		reversal = LedgerEntry(
			user_id=user_id,
			domain=orig.domain,
			action=f"reverse:{orig.action}",
			points=-orig.points,
			related_entry_id=orig.id,
			evidence_ref=orig.evidence_ref,
			evidence_status=orig.evidence_status,
		)
		self.session.add(reversal)
		self.session.commit()
		self.session.refresh(reversal)
		return reversal

	def flag_evidence(self, entry_id: int, status: str) -> LedgerEntry:
		if status not in {EvidenceStatusEnum.YELLOW, EvidenceStatusEnum.RED}:
			raise ValueError("Invalid flag status")
		entry = self.session.get(LedgerEntry, entry_id)
		if entry is None:
			raise ValueError("Entry not found")
		entry.evidence_status = status
		self.session.commit()
		self.session.refresh(entry)
		return entry


