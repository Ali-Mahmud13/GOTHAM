"""Shared SlowAPI rate limiter (IP-based; enable via RATE_LIMIT_ENABLED)."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core import config

limiter = Limiter(key_func=get_remote_address, enabled=config.RATE_LIMIT_ENABLED)
