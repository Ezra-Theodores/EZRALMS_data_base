"""
/api/cache/*  -  Cache statistics diagnostic endpoint.

Returns hit/miss counters for all three TTL caches (profile, leaderboard, RAG).
Read-only — no mutations.
"""

from flask import Blueprint, jsonify

from ._cache import cache_stats

bp = Blueprint("cache_stats", __name__, url_prefix="/api/cache")


@bp.route("/stats")
def stats():
    """Return current hit/miss counters for all caches."""
    cs = cache_stats()
    return jsonify({
        "success": True,
        "profile_hits": cs.profile_hits,
        "profile_misses": cs.profile_misses,
        "leaderboard_hits": cs.leaderboard_hits,
        "leaderboard_misses": cs.leaderboard_misses,
        "rag_hits": cs.rag_hits,
        "rag_misses": cs.rag_misses,
    })
