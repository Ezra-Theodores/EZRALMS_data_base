"""
/api/quizzes/*  -  Backend for the (previously orphan) RAG DB Quiz Manager UI
                   at DATA_HOUSE_EZRALMS/public/index.html.

Reads questions and quizzes from data_house.db (BM25-indexed by data_house.py)
plus the structured tables synced from Firestore.

Phase 1 endpoints:
    GET  /api/quizzes/ping
    GET  /api/quizzes/stats
    GET  /api/quizzes/questions    ? filters: grade, topic, difficulty, hasImage, q, page, limit
    GET  /api/quizzes/quizzes      list all quizzes (paginated)
    GET  /api/quizzes/quiz/<id>    quiz + its questions

Phase 2 will add quiz assembler endpoints (create/update/export).
"""

import json
from flask import Blueprint, jsonify, request

from ._db import get_data_house_db, close_all

bp = Blueprint("quiz_manager", __name__, url_prefix="/api/quizzes")
bp.teardown_request(close_all)


@bp.route("/ping")
def ping():
    return jsonify({"success": True, "blueprint": "quiz_manager"})


def _table_exists(cur, table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


@bp.route("/stats")
def stats():
    try:
        cur = get_data_house_db().cursor()
        out = {"total_questions": 0, "total_quizzes": 0, "by_topic": {}, "by_grade": {}}

        if _table_exists(cur, "questions"):
            cur.execute("SELECT COUNT(*) AS c FROM questions")
            out["total_questions"] = cur.fetchone()["c"]

            cur.execute("SELECT topic, COUNT(*) AS c FROM questions GROUP BY topic")
            out["by_topic"] = {row["topic"] or "Unknown": row["c"] for row in cur.fetchall()}

        if _table_exists(cur, "quizzes"):
            cur.execute("SELECT COUNT(*) AS c FROM quizzes")
            out["total_quizzes"] = cur.fetchone()["c"]

            cur.execute("SELECT grade, COUNT(*) AS c FROM quizzes GROUP BY grade")
            out["by_grade"] = {row["grade"] or "Unknown": row["c"] for row in cur.fetchall()}

        return jsonify({"success": True, "data": out})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/questions")
def questions():
    """Filterable, paginated question list."""
    try:
        cur = get_data_house_db().cursor()
        if not _table_exists(cur, "questions"):
            return jsonify({"success": True, "data": [], "total": 0, "page": 1})

        grade = request.args.get("grade")
        topic = request.args.get("topic")
        has_image = request.args.get("hasImage")
        q = request.args.get("q", "").strip()
        page = max(1, int(request.args.get("page", "1")))
        limit = max(1, min(200, int(request.args.get("limit", "20"))))
        offset = (page - 1) * limit

        conditions, params = [], []
        if topic:
            conditions.append("q.topic = ?"); params.append(topic)
        if grade:
            conditions.append("qz.grade = ?"); params.append(grade)
        if has_image == "true":
            conditions.append("q.image IS NOT NULL AND q.image != ''")
        elif has_image == "false":
            conditions.append("(q.image IS NULL OR q.image = '')")
        if q:
            conditions.append("(q.id_q LIKE ? OR q.en_q LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        base_from = "FROM questions q LEFT JOIN quizzes qz ON q.quiz_id = qz.quiz_id"

        cur.execute(f"SELECT COUNT(*) AS c {base_from} {where}", params)
        total = cur.fetchone()["c"]

        cur.execute(
            f"""SELECT q.*, qz.title AS quiz_title, qz.grade AS grade
                {base_from} {where}
                ORDER BY q.id DESC LIMIT ? OFFSET ?""",
            params + [limit, offset],
        )
        rows = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("options"):
                try:
                    d["options"] = json.loads(d["options"])
                except (json.JSONDecodeError, TypeError):
                    pass
            rows.append(d)

        return jsonify({
            "success": True, "data": rows, "total": total,
            "page": page, "limit": limit,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/quizzes")
def quizzes_list():
    try:
        cur = get_data_house_db().cursor()
        if not _table_exists(cur, "quizzes"):
            return jsonify({"success": True, "data": [], "total": 0})

        page = max(1, int(request.args.get("page", "1")))
        limit = max(1, min(200, int(request.args.get("limit", "20"))))
        offset = (page - 1) * limit

        cur.execute("SELECT COUNT(*) AS c FROM quizzes")
        total = cur.fetchone()["c"]

        cur.execute(
            "SELECT quiz_id, title, description, grade, subject, total_questions "
            "FROM quizzes ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        data = [dict(r) for r in cur.fetchall()]
        return jsonify({"success": True, "data": data, "total": total, "page": page, "limit": limit})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/quiz/<quiz_id>")
def quiz_detail(quiz_id):
    try:
        cur = get_data_house_db().cursor()
        if not _table_exists(cur, "quizzes"):
            return jsonify({"success": False, "error": "quizzes table not present"}), 404

        cur.execute("SELECT * FROM quizzes WHERE quiz_id = ?", (quiz_id,))
        quiz = cur.fetchone()
        if not quiz:
            return jsonify({"success": False, "error": "Quiz not found"}), 404

        cur.execute("SELECT * FROM questions WHERE quiz_id = ? ORDER BY id", (quiz_id,))
        questions = []
        for r in cur.fetchall():
            d = dict(r)
            if d.get("options"):
                try:
                    d["options"] = json.loads(d["options"])
                except (json.JSONDecodeError, TypeError):
                    pass
            questions.append(d)

        return jsonify({"success": True, "quiz": dict(quiz), "questions": questions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
