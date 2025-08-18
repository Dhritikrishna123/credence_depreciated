
from __future__ import annotations

from dataclasses import dataclass
import hmac
import hashlib
import json
from typing import Any, Dict

import requests

from ..config import Settings


@dataclass
class WebhookClient:
    settings: Settings

    def is_enabled(self) -> bool:
        return bool(self.settings.webhook_url and self.settings.webhook_secret)

    def _sign(self, payload: str) -> str:
        secret = (self.settings.webhook_secret or "").encode("utf-8")
        return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if not self.is_enabled():
            return
        body = json.dumps({"type": event_type, "data": data}, separators=(",", ":"))
        signature = self._sign(body)
        try:
            requests.post(
                self.settings.webhook_url,  # type: ignore[arg-type]
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Credence-Event": event_type,
                    "X-Credence-Signature": signature,
                },
                timeout=self.settings.webhook_timeout_seconds,
            )
        except Exception:
            # Keep main flow resilient; optional retry pipeline can be added later
            pass



