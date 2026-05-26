"""
/api/attendance/*  -  Ported from app.py

Search, stats, and single-record lookup for attendance records in
ezralms.db (synced from Firestore by sync_attendance.py).
"""

import json
from flask import Blueprint, jsonify, request, make_response
from ._cache import cache_clear
from ._db import get_attendance_db, close_all

bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")
bp.teardown_request(close_all)


@bp.route("/ping")
def ping():
    return jsonify({"success": True, "blueprint": "attendance"})


@bp.route("/stats")
def stats():
    try:
        cur = get_attendance_db().cursor()

        cur.execute("SELECT COUNT(*) AS total FROM attendance")
        total = cur.fetchone()["total"]

        cur.execute("SELECT status, COUNT(*) AS count FROM attendance GROUP BY status")
        by_status = {row["status"]: row["count"] for row in cur.fetchall()}

        cur.execute(
            "SELECT MIN(attendance_date) AS min_date, MAX(attendance_date) AS max_date FROM attendance"
        )
        dr = cur.fetchone()

        resp = jsonify({
            "success": True,
            "data": {
                "total_records": total,
                "by_status": by_status,
                "date_range": {"min": dr["min_date"], "max": dr["max_date"]},
            },
        })
        resp.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=300"
        return resp
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/search")
def search():
    try:
        cur = get_attendance_db().cursor()

        filters = {
            "student_name LIKE ?": request.args.get("student_name", "").strip(),
            "student_id LIKE ?": request.args.get("student_id", "").strip(),
            "class_name LIKE ?": request.args.get("class_name", "").strip(),
            "status = ?": request.args.get("status", "").strip(),
            "attendance_date >= ?": request.args.get("date_from", "").strip(),
            "attendance_date <= ?": request.args.get("date_to", "").strip(),
        }

        conditions, params = [], []
        for clause, value in filters.items():
            if not value:
                continue
            conditions.append(clause)
            params.append(f"%{value}%" if "LIKE" in clause else value)

        query = "SELECT * FROM attendance"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY attendance_date DESC, student_name ASC"

        cur.execute(query, params)
        records = []
        for row in cur.fetchall():
            record = dict(row)
            if record.get("raw_data"):
                try:
                    record["raw_data_parsed"] = json.loads(record["raw_data"])
                except (json.JSONDecodeError, ValueError):
                    pass
            records.append(record)

        resp = jsonify({"success": True, "count": len(records), "data": records})
        resp.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=300"
        return resp
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/record/<firestore_id>")
def get_record(firestore_id):
    try:
        cur = get_attendance_db().cursor()
        cur.execute("SELECT * FROM attendance WHERE firestore_id = ?", (firestore_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({"success": False, "error": "Record not found"}), 404

        record = dict(row)
        if record.get("raw_data"):
            try:
                record["raw_data_parsed"] = json.loads(record["raw_data"])
            except (json.JSONDecodeError, ValueError):
                pass
        resp = jsonify({"success": True, "data": record})
        resp.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=300"
        return resp
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
