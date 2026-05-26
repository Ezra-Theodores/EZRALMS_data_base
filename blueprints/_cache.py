"""
Shared TTL cache module using cachetools.

Provides three named TTL caches plus a thread-safe stats counter.
Cleared in full after every successful Firebase sync.
"""
from dataclasses import dataclass
import threading

from cachetools import TTLCache

# ── Cache instances ────────────────────────────────────────────────────────────

ProfileCache = TTLCache(maxsize=500, ttl=120)
"""TTL=2 min, keyed by student_id."""

LeaderboardCache = TTLCache(maxsize=200, ttl=60)
"""TTL=1 min, singleton (no key needed – single result set)."""

RagCache = TTLCache(maxsize=1000, ttl=300)
"""TTL=5 min, keyed by hash(q) + str(k)."""

# ── CacheStats ─────────────────────────────────────────────────────────────────

_stats_lock = threading.Lock()


@dataclass
class CacheStats:
    profile_hits: int = 0
    profile_misses: int = 0
    leaderboard_hits: int = 0
    leaderboard_misses: int = 0
    rag_hits: int = 0
    rag_misses: int = 0


_stats = CacheStats()


def cache_clear():
    """Clear ALL TTL caches — call after a successful Firebase sync."""
    ProfileCache.clear()
    LeaderboardCache.clear()
    RagCache.clear()
    with _stats_lock:
        global _stats
        _stats = CacheStats()


def cache_stats() -> CacheStats:
    return _stats
