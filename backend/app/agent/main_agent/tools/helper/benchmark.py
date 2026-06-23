"""
GOTHAM Pipeline Benchmarking Utility
=====================================
Measures wall-clock time for the key stages targeted by the AI/ML improvement plan.
Add BENCHMARK=true to your .env (or set the env var) to enable detailed timing logs.

Tracked stages:
  - Model load / init        (3.1 — Singleton Caching)
  - Maternal pipeline total  (3.3 — Parallel Execution)
  - Fetal pipeline total     (3.3 — Parallel Execution)
  - check_clarity LLM calls  (4.1 — Combined Classifier)
  - Full request (start → respond node)
"""

import time
import logging
import os
import functools
from contextlib import asynccontextmanager, contextmanager
from typing import Optional

logger = logging.getLogger("gotham.benchmark")

# Enable via env var: BENCHMARK=true
_ENABLED = os.getenv("BENCHMARK", "false").lower() in ("true", "1", "yes")

# In-memory store for the current request's timings
# Keyed by label → list of elapsed seconds (supports multiple calls)
_timings: dict[str, list[float]] = {}


def is_enabled() -> bool:
    return _ENABLED


def reset():
    """Clear all timings — call at the start of each request."""
    _timings.clear()


def record(label: str, elapsed: float):
    """Store a timing result."""
    _timings.setdefault(label, []).append(elapsed)
    logger.info(f"[BENCHMARK] {label}: {elapsed:.3f}s")


def summary() -> str:
    """Return a formatted summary of all recorded timings."""
    if not _timings:
        return "[BENCHMARK] No timings recorded."
    lines = ["", "=" * 55, "  GOTHAM PIPELINE BENCHMARK SUMMARY", "=" * 55]
    total = 0.0
    for label, times in _timings.items():
        avg = sum(times) / len(times)
        total += avg
        calls = f"(x{len(times)})" if len(times) > 1 else ""
        lines.append(f"  {label:<40} {avg:.3f}s {calls}")
    lines.append("-" * 55)
    lines.append(f"  {'TOTAL (approx)':<40} {total:.3f}s")
    lines.append("=" * 55)
    
    out_str = "\n".join(lines)
    
    # Also write to a local file so we can read the exact numbers
    try:
        import os
        log_file = os.path.join(os.path.dirname(__file__), "benchmark_results.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(out_str + "\n\n")
    except Exception:
        pass
        
    return out_str


# ── Context managers ──────────────────────────────────────────

@contextmanager
def timer(label: str):
    """Sync context manager. Usage: with timer('my step'): ..."""
    if not _ENABLED:
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        record(label, time.perf_counter() - start)


@asynccontextmanager
async def async_timer(label: str):
    """Async context manager. Usage: async with async_timer('my step'): ..."""
    if not _ENABLED:
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        record(label, time.perf_counter() - start)


# ── Decorators ────────────────────────────────────────────────

def timed(label: Optional[str] = None):
    """
    Decorator for sync or async functions.
    Usage:
        @timed("Model Load: FHP")
        async def predict_fetal_health(...): ...
    """
    def decorator(fn):
        lbl = label or fn.__qualname__

        if _ENABLED:
            if _is_async(fn):
                @functools.wraps(fn)
                async def async_wrapper(*args, **kwargs):
                    start = time.perf_counter()
                    result = await fn(*args, **kwargs)
                    record(lbl, time.perf_counter() - start)
                    return result
                return async_wrapper
            else:
                @functools.wraps(fn)
                def sync_wrapper(*args, **kwargs):
                    start = time.perf_counter()
                    result = fn(*args, **kwargs)
                    record(lbl, time.perf_counter() - start)
                    return result
                return sync_wrapper
        # If benchmarking disabled, return fn unchanged
        return fn
    return decorator


def _is_async(fn) -> bool:
    import asyncio
    return asyncio.iscoroutinefunction(fn)
