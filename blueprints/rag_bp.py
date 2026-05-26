import os
import sys
import hashlib
from flask import Blueprint, jsonify, request, make_response, current_app

from . import _cache

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


_bp = Blueprint("rag", __name__, url_prefix="/api/rag")
# Alias so existing @bp.route decorators keep working
bp = _bp

_dh = None  # global DataHouse instance


def _get_dh():
    global _dh
    if _dh is None:
        from data_house import DataHouse
        _dh = DataHouse(base_path=ROOT)
    return _dh


def _get_unified_db_path():
    """Path to the unified SQLite database."""
    return os.path.join(ROOT, "ezralms_unified.db")


@bp.route("/ping")
def ping():
    return jsonify({"success": True, "blueprint": "rag"})


@bp.route("/stats")
def stats():
    try:
        return jsonify({"success": True, "data": _get_dh().get_statistics()})
    except Exception as e:
        current_app.logger.error(f"RAG stats failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/search")
def search():
    """Query params: q (required), k (default 10), type (source_type filter)."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"success": False, "error": "Missing 'q' parameter"}), 400
    k = int(request.args.get("k", "10"))
    source_type = request.args.get("type")

    # ── RAG cache: key = hash(q) + str(k) ─────────────────────────────────
    cache_key = f"{hash(q)}:{k}"
    cached = _cache.RagCache.get(cache_key)
    if cached is not None:
        with _cache._stats_lock:
            _cache.cache_stats().rag_hits += 1
        resp = jsonify(cached)
        resp.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=600"
        return resp

    with _cache._stats_lock:
        _cache.cache_stats().rag_misses += 1

    try:
        results = _get_dh().search(q, k=k, source_type=source_type)
        data = {
            "success": True,
            "query": q,
            "count": len(results),
            "results": [
                {
                    "score": r.score,
                    "source_type": r.document.source_type,
                    "source_path": r.document.source_path,
                    "content": r.document.content,
                    "metadata": r.document.metadata,
                }
                for r in results
            ],
        }
        _cache.RagCache[cache_key] = data
        resp = jsonify(data)
        resp.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=600"
        return resp
    except Exception as e:
        current_app.logger.error(f"RAG search failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/context")
def context():
    """Build a RAG context string for a query."""
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"success": False, "error": "Missing 'q' parameter"}), 400
    k = int(request.args.get("k", "5"))
    try:
        resp = jsonify({"success": True, "context": _get_dh().generate_context(q, k=k)})
        resp.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=600"
        return resp
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/rebuild", methods=["POST"])
def rebuild():
    """Force-rebuild the vector index from SQLite tables."""
    try:
        # Rebuild in same thread as connection was created
        _get_dh().rebuild_index(force=True)
        return jsonify({"success": True, "message": "Index rebuilt"})
    except Exception as e:
        current_app.logger.error(f"RAG rebuild failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/sql", methods=["GET", "POST"])
def sql_query():
    """
    Execute arbitrary read-only SQL against the unified database.

    GET ?sql=SELECT ...&limit=50
    POST body { "sql": "...", "limit": 50 }

    Returns: { success, columns, rows, count }
    Only SELECT statements are allowed.
    """
    import sqlite3

    sql = None
    limit = 100

    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        sql = (body.get("sql") or "").strip()
        limit = int(body.get("limit", 100))
    else:
        sql = request.args.get("sql", "").strip()
        limit = int(request.args.get("limit", "100"))

    if not sql:
        return jsonify({"success": False, "error": "Missing 'sql' parameter"}), 400

    # Enforce read-only
    normalized = sql.lower().strip()
    if not normalized.startswith("select"):
        return jsonify({"success": False, "error": "Only SELECT statements are allowed"}), 400

    try:
        conn = sqlite3.connect(_get_unified_db_path())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchmany(limit + 1)
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        columns = [desc[0] for desc in cur.description] if cur.description else []
        conn.close()

        return jsonify({
            "success": True,
            "columns": columns,
            "rows": [dict(zip(columns, r)) for r in rows],
            "count": len(rows),
            "has_more": has_more,
        })
    except Exception as e:
        current_app.logger.error(f"RAG SQL failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
