"""
/api/curriculum/*  -  Curriculum (Grades -> Classes -> Topics -> Sub-topics ->
                      Materials -> Quizzes -> Questions) + Users.

Uses the legacy_* tables for the curriculum tree (sample seed data with
grade_id linkage) and the rich `users` table from data_house for user lists.

Tables used:
    grades, legacy_classes, legacy_topics, sub_topics, materials,
    legacy_quizzes, quiz_questions   (curriculum tree)
    users                            (rich Firebase users — 93 rows)
"""

import json
import os
from flask import Blueprint, jsonify, request, send_from_directory

from ._db import get_unified_db, close_all

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_HOUSE = os.path.join(ROOT, "DATA_HOUSE_EZRALMS")
os.makedirs(DATA_HOUSE, exist_ok=True)

bp = Blueprint("curriculum", __name__, url_prefix="/api/curriculum")
bp.teardown_request(close_all)


@bp.route("/ping")
def ping():
    return jsonify({"success": True, "blueprint": "curriculum"})


@bp.route("/stats")
def stats():
    try:
        cur = get_unified_db().cursor()
        out = {}

        cur.execute("SELECT role, COUNT(*) AS count FROM users GROUP BY role")
        out["users_by_role"] = {row["role"]: row["count"] for row in cur.fetchall()}

        for table, key in [
            ("grades", "grades_count"),
            ("legacy_classes", "classes_count"),
            ("legacy_topics", "topics_count"),
            ("sub_topics", "sub_topics_count"),
            ("legacy_quizzes", "quizzes_count"),
            ("quiz_questions", "questions_count"),
        ]:
            cur.execute(f"SELECT COUNT(*) AS count FROM {table}")
            out[key] = cur.fetchone()["count"]

        cur.execute("SELECT material_type, COUNT(*) AS count FROM materials GROUP BY material_type")
        out["materials_by_type"] = {row["material_type"]: row["count"] for row in cur.fetchall()}

        resp = jsonify({"success": True, "data": out})
        resp.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=300"
        return resp
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/tree/<entity_type>")
def get_tree(entity_type):
    """Hierarchical curriculum tree, or users list."""
    try:
        cur = get_unified_db().cursor()

        if entity_type == "curriculum":
            cur.execute(
                "SELECT grade_id, grade_number, grade_name, description "
                "FROM grades ORDER BY grade_number"
            )
            tree = []
            for grade in cur.fetchall():
                grade_node = {
                    "id": grade["grade_id"], "type": "grade",
                    "number": grade["grade_number"], "name": grade["grade_name"],
                    "description": grade["description"], "children": [],
                }

                cur.execute(
                    "SELECT class_id, class_name, class_code, section "
                    "FROM legacy_classes WHERE grade_id = ? ORDER BY class_name",
                    (grade["grade_id"],),
                )
                for c in cur.fetchall():
                    class_node = {
                        "id": c["class_id"], "type": "class", "name": c["class_name"],
                        "code": c["class_code"], "section": c["section"], "children": [],
                    }

                    cur.execute(
                        "SELECT topic_id, topic_name, description, order_index "
                        "FROM legacy_topics WHERE class_id = ? "
                        "ORDER BY order_index, topic_name",
                        (c["class_id"],),
                    )
                    for t in cur.fetchall():
                        topic_node = {
                            "id": t["topic_id"], "type": "topic", "name": t["topic_name"],
                            "description": t["description"], "children": [],
                        }

                        cur.execute(
                            "SELECT sub_topic_id, sub_topic_name, description, order_index "
                            "FROM sub_topics WHERE topic_id = ? "
                            "ORDER BY order_index, sub_topic_name",
                            (t["topic_id"],),
                        )
                        for st in cur.fetchall():
                            st_node = {
                                "id": st["sub_topic_id"], "type": "sub_topic",
                                "name": st["sub_topic_name"], "description": st["description"],
                                "children": [],
                            }

                            cur.execute(
                                "SELECT material_id, material_title, material_type, "
                                "description, file_path "
                                "FROM materials WHERE sub_topic_id = ? "
                                "ORDER BY material_title",
                                (st["sub_topic_id"],),
                            )
                            for m in cur.fetchall():
                                st_node["children"].append({
                                    "id": m["material_id"], "type": "material",
                                    "title": m["material_title"],
                                    "material_type": m["material_type"],
                                    "description": m["description"],
                                    "file_path": m["file_path"],
                                })

                            cur.execute(
                                "SELECT quiz_id, quiz_title, description, difficulty, "
                                "passing_score, time_limit "
                                "FROM legacy_quizzes WHERE sub_topic_id = ? "
                                "ORDER BY created_at",
                                (st["sub_topic_id"],),
                            )
                            for q in cur.fetchall():
                                st_node["children"].append({
                                    "id": q["quiz_id"], "type": "quiz",
                                    "title": q["quiz_title"], "description": q["description"],
                                    "difficulty": q["difficulty"],
                                    "passing_score": q["passing_score"],
                                    "time_limit": q["time_limit"],
                                })

                            topic_node["children"].append(st_node)
                        class_node["children"].append(topic_node)
                    grade_node["children"].append(class_node)
                tree.append(grade_node)
            resp = jsonify({"success": True, "data": tree})
            resp.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=300"
            return resp

        if entity_type == "users":
            # Rich users from Firebase sync
            role = request.args.get("role")
            search = request.args.get("search")

            query = "SELECT user_id, name, email, role, phone, avatar_url, xp FROM users WHERE 1=1"
            params = []
            if role:
                query += " AND role = ?"; params.append(role)
            if search:
                query += " AND (name LIKE ? OR email LIKE ? OR user_id LIKE ?)"
                params.extend([f"%{search}%"] * 3)
            query += " ORDER BY name"

            cur.execute(query, params)
            users = [dict(u) for u in cur.fetchall()]
            resp = jsonify({"success": True, "count": len(users), "data": users})
            resp.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=300"
            return resp

        return jsonify({"success": False, "error": "Invalid entity type"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ── CRUD ──────────────────────────────────────────────────────────────────
# CRUD operates on the curriculum seed tables (grades + legacy_*) which use
# stable schemas the source app originally targeted.

_INSERT_SQL = {
    "grade": (
        """INSERT INTO grades (grade_id, grade_number, grade_name, description, curriculum_type)
           VALUES (?, ?, ?, ?, ?)""",
        ["grade_id", "grade_number", "grade_name", "description", "curriculum_type"],
    ),
    "class": (
        """INSERT INTO legacy_classes (class_id, class_name, grade_id, class_code, section)
           VALUES (?, ?, ?, ?, ?)""",
        ["class_id", "class_name", "grade_id", "class_code", "section"],
    ),
    "topic": (
        """INSERT INTO legacy_topics (topic_id, topic_name, class_id, description, order_index)
           VALUES (?, ?, ?, ?, ?)""",
        ["topic_id", "topic_name", "class_id", "description", "order_index"],
    ),
    "sub_topic": (
        """INSERT INTO sub_topics (sub_topic_id, sub_topic_name, topic_id, description, order_index)
           VALUES (?, ?, ?, ?, ?)""",
        ["sub_topic_id", "sub_topic_name", "topic_id", "description", "order_index"],
    ),
    "material": (
        """INSERT INTO materials (material_id, material_title, sub_topic_id, material_type, description, file_path)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ["material_id", "material_title", "sub_topic_id", "material_type", "description", "file_path"],
    ),
    "quiz": (
        """INSERT INTO legacy_quizzes (quiz_id, quiz_title, sub_topic_id, description, difficulty, passing_score, time_limit)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ["quiz_id", "quiz_title", "sub_topic_id", "description", "difficulty", "passing_score", "time_limit"],
    ),
}

_TABLE_MAP = {
    "grade": "grades", "class": "legacy_classes", "topic": "legacy_topics",
    "sub_topic": "sub_topics", "material": "materials", "quiz": "legacy_quizzes",
}


@bp.route("/<entity_type>", methods=["POST"])
def create_entity(entity_type):
    if entity_type not in _INSERT_SQL:
        return jsonify({"success": False, "error": "Unknown entity"}), 400
    try:
        sql, fields = _INSERT_SQL[entity_type]
        data = request.json or {}
        params = [data.get(f) for f in fields]

        db = get_unified_db()
        db.cursor().execute(sql, params)
        db.commit()
        return jsonify({"success": True, "message": f"{entity_type} created"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/<entity_type>/<id>", methods=["PUT", "DELETE"])
def update_or_delete(entity_type, id):
    if entity_type not in _TABLE_MAP:
        return jsonify({"success": False, "error": "Unknown entity"}), 400
    try:
        table = _TABLE_MAP[entity_type]
        id_col = f"{entity_type}_id"
        db = get_unified_db()
        cur = db.cursor()

        if request.method == "DELETE":
            cur.execute(f"DELETE FROM {table} WHERE {id_col} = ?", (id,))
            db.commit()
            return jsonify({"success": True, "message": f"{entity_type} deleted"})

        data = request.json or {}
        fields, values = [], []
        for k, v in data.items():
            if k in ("id", "created_at"):
                continue
            fields.append(f"{k} = ?"); values.append(v)
        values.append(id)
        cur.execute(f"UPDATE {table} SET {', '.join(fields)} WHERE {id_col} = ?", values)
        db.commit()
        return jsonify({"success": True, "message": f"{entity_type} updated"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/export/<entity_type>")
def export_data(entity_type):
    """Export curriculum tree or users list to DATA_HOUSE_EZRALMS as JSON."""
    try:
        if entity_type == "curriculum":
            payload = get_tree("curriculum").get_json()
            fname = "curriculum_export.json"
        elif entity_type == "users":
            cur = get_unified_db().cursor()
            cur.execute("SELECT * FROM users ORDER BY name")
            users = [dict(u) for u in cur.fetchall()]
            payload = {"count": len(users), "users": users}
            fname = "users_export.json"
        else:
            return jsonify({"success": False, "error": "Invalid export type"}), 400

        path = os.path.join(DATA_HOUSE, fname)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return jsonify({
            "success": True, "message": f"{entity_type} exported",
            "file_path": path, "download_url": f"/api/curriculum/download/{fname}",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(DATA_HOUSE, filename, as_attachment=True)
