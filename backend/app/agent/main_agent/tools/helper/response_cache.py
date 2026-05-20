"""
GOTHAM In-Memory Response Cache
=================================
Caches final LLM responses for identical queries to the same patient.
Cache key: sha256(patient_id + normalized_query)

Design decisions:
  - In-memory only (wiped on server restart) — ensures clinical freshness.
  - Assessment responses (maternal/fetal/both) are NEVER cached — they run
    the ML pipeline and each run may reflect updated patient data.
  - Only conversational / RAG / follow-up responses are cached.
  - Cache is invalidated per-patient when a new assessment is stored.
  - Max 256 entries (LRU-style eviction via OrderedDict) to cap memory use.

Enable via BENCHMARK=true env var for hit/miss logging.
"""

import hashlib
import logging
import os
from collections import OrderedDict

logger = logging.getLogger("gotham.response_cache")

_ENABLED = os.getenv("RESPONSE_CACHE", "true").lower() in ("true", "1", "yes")
_MAX_SIZE = 256  # max cached entries

# OrderedDict used as a simple LRU: most-recently-used entries move to the end.
# { cache_key: response_text }
_cache: OrderedDict[str, str] = OrderedDict()

# Per-patient key set — used for targeted invalidation.
# { patient_id: set of cache_keys }
_patient_keys: dict[str, set[str]] = {}


def _make_key(patient_id: str, query: str) -> str:
    """Build a stable cache key from patient ID and normalised query text."""
    normalised = " ".join(query.lower().split())
    raw = f"{patient_id}|{normalised}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get(patient_id: str, query: str) -> str | None:
    """Return a cached response, or None on a cache miss."""
    if not _ENABLED or not patient_id or patient_id == "NONE":
        return None
    key = _make_key(patient_id, query)
    if key in _cache:
        # Move to end (most-recently-used)
        _cache.move_to_end(key)
        logger.info(f"[CACHE HIT]  patient={patient_id}  key={key[:12]}…")
        return _cache[key]
    logger.debug(f"[CACHE MISS] patient={patient_id}  key={key[:12]}…")
    return None


def put(patient_id: str, query: str, response: str) -> None:
    """Store a response in the cache."""
    if not _ENABLED or not patient_id or patient_id == "NONE":
        return
    key = _make_key(patient_id, query)
    _cache[key] = response
    _cache.move_to_end(key)
    # Track key per patient for invalidation
    _patient_keys.setdefault(patient_id, set()).add(key)
    # Evict oldest if over capacity
    while len(_cache) > _MAX_SIZE:
        oldest_key, _ = _cache.popitem(last=False)
        logger.debug(f"[CACHE EVICT] key={oldest_key[:12]}…")
    logger.info(f"[CACHE STORE] patient={patient_id}  key={key[:12]}…  size={len(_cache)}")


def invalidate_patient(patient_id: str) -> None:
    """
    Remove all cached entries for a given patient.
    Called whenever a new assessment (maternal/fetal/both) is run,
    since the patient's risk profile may have changed.
    """
    if not patient_id or patient_id == "NONE":
        return
    keys = _patient_keys.pop(patient_id, set())
    for key in keys:
        _cache.pop(key, None)
    if keys:
        logger.info(f"[CACHE INVALIDATE] patient={patient_id}  removed {len(keys)} entries")


def stats() -> dict:
    """Return cache stats for logging/monitoring."""
    return {"size": len(_cache), "patients_tracked": len(_patient_keys), "enabled": _ENABLED}
