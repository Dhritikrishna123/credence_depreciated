from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address


# Shared limiter for routers to import and use decorators
limiter = Limiter(key_func=get_remote_address)


