"""
/api/sync/*  -  Firebase Firestore -> local SQLite sync

Initialises firebase_admin lazily (so the unified app still boots without
credentials available). Syncs users and attendance into ezralms_complete.db,
mirroring the /api/sync logic that lived inside app_complete.py.
"""

import json
import os
from datetime import datetime
from flask import Blueprint, jsonify, current_app

from ._cache import cache_clear
from ._db import get_complete_db, close_all

bp = Blueprint("firebase_sync", __name__, url_prefix="/api/sync")
bp.teardown_request(close_all)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CRED = os.path.join(ROOT, "firebase_credentials.json")


@bp.route("/ping")
def ping():
    return jsonify({"success": True, "blueprint": "firebase_sync"})


def _firestore_client():
    """Lazy-init firebase_admin; returns the Firestore client or raises."""
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", DEFAULT_CRED)
        if not os.path.exists(cred_path):
            raise RuntimeError(f"Firebase credentials not found at {cred_path}")
        firebase_admin.initialize_app(credentials.Certificate(cred_path))
    return firestore.client()


@bp.route("/all", methods=["POST"])
def sync_users_and_attendance():
    """
    Full Firebase -> SQLite sync:
      - users
      - attendance
      - quiz_attempts
      - student_activities

    This is what the "Update" button on the dashboard calls.
    """
    def _serialize(obj):
        return obj.isoformat() if hasattr(obj, "isoformat") else str(obj)

    try:
        fs = _firestore_client()
        db = get_complete_db()
        cur = db.cursor()

        # ── Users ──────────────────────────────────────────────────────────
        users_synced = 0
        valid_roles = ("student", "teacher", "admin", "parent")
        for doc in fs.collection("users").stream():
            data = doc.to_dict() or {}
            user_id = data.get("uid") or data.get("id") or doc.id
            raw_role = str(data.get("role", "student")).lower()
            role = raw_role if raw_role in valid_roles else "student"

            # Extract best name — displayName or profile.firstName+lastName
            profile = data.get("profile", {}) or {}
            display = (
                data.get("displayName")
                or f"{profile.get('firstName','')} {profile.get('lastName','')}".strip()
                or data.get("username", "")
            )
            # Keep full Firestore doc as raw_json for reference
            raw_json = json.dumps(data, default=_serialize)

            cur.execute(
                """INSERT OR REPLACE INTO users
                   (user_id, name, email, role, phone, xp, raw_json,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                (
                    user_id,
                    display,
                    data.get("email", f"{user_id}@ezralms.local"),
                    role,
                    profile.get("phone") or data.get("phone", ""),
                    0,
                    raw_json,
                ),
            )
            users_synced += 1

        # ── Attendance ─────────────────────────────────────────────────────
        attendance_synced = 0
        for doc in fs.collection("attendance").stream():
            data = doc.to_dict() or {}
            try:
                cur.execute(
                    """INSERT OR REPLACE INTO attendance
                       (firestore_id, student_id, student_name, class_name,
                        attendance_date, status, raw_data)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        doc.id,
                        data.get("student_id", ""),
                        data.get("student_name", ""),
                        data.get("class_name", ""),
                        data.get("date", ""),
                        data.get("status", ""),
                        json.dumps(data, default=_serialize),
                    ),
                )
                attendance_synced += 1
            except Exception as e:
                current_app.logger.warning(f"attendance row {doc.id} skipped: {e}")

        # ── Quiz Attempts ─────────────────────────────────────────────────
        quiz_synced = 0
        quiz_skipped = 0
        for doc in fs.collection("quiz_attempts").stream():
            data = doc.to_dict() or {}
            try:
                # Parse timestamps
                started = data.get("startedAt") or ""
                completed = data.get("completedAt") or ""
                if hasattr(completed, "isoformat"):
                    completed = completed.isoformat()
                if hasattr(started, "isoformat"):
                    started = started.isoformat()
                started = str(started)
                completed = str(completed)

                # Build answers JSON
                answers = {
                    "answers": data.get("answers", {}),
                    "answerTexts": data.get("answerTexts", {}),
                    "textAnswers": data.get("textAnswers", {}),
                }
                answers_json = json.dumps(answers)

                raw_json = json.dumps({
                    "userId": data.get("userId", ""),
                    "quizId": data.get("quizId", ""),
                    "quizTitle": data.get("quizTitle", ""),
                    "status": data.get("status", ""),
                    "score": data.get("score", 0),
                    "maxScore": data.get("maxScore", 0),
                    "correctCount": data.get("correctCount", 0),
                    "totalQuestions": data.get("totalQuestions", 0),
                    "passingScore": data.get("passingScore", 0),
                    "completedAt": completed,
                    "startedAt": started,
                    "timeTaken": data.get("timeTaken", 0),
                    "classId": data.get("classId", ""),
                    "attemptNumber": data.get("attemptNumber", 1),
                    "passed": data.get("passed", False),
                    "answers": answers,
                }, default=_serialize)

                # Try UPDATE first (doc.id exists), else INSERT
                cur.execute("SELECT id FROM quiz_attempts WHERE id = ?", (doc.id,))
                exists = cur.fetchone() is not None

                if exists:
                    cur.execute("""
                        UPDATE quiz_attempts SET
                          attempt_id=?, quiz_id=?, student_id=?, student_name=?,
                          score=?, max_score=?, duration=?, answers=?,
                          started_at=?, completed_at=?, raw_json=?
                        WHERE id=?
                    """, (
                        doc.id, data.get("quizId",""), data.get("userId",""),
                        data.get("studentName",""),
                        float(data.get("score",0)), float(data.get("maxScore",0)),
                        int(data.get("timeTaken",0) or 0),
                        answers_json, started, completed, raw_json,
                        doc.id,
                    ))
                else:
                    cur.execute("""
                        INSERT INTO quiz_attempts
                          (id, attempt_id, quiz_id, student_id, student_name,
                           score, max_score, duration, answers,
                           started_at, completed_at, raw_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc.id, doc.id, data.get("quizId",""), data.get("userId",""),
                        data.get("studentName",""),
                        float(data.get("score",0)), float(data.get("maxScore",0)),
                        int(data.get("timeTaken",0) or 0),
                        answers_json, started, completed, raw_json,
                    ))
                quiz_synced += 1
            except Exception as e:
                quiz_skipped += 1
                current_app.logger.warning(f"quiz_attempt {doc.id} skipped: {e}")

        db.commit()

        # ── Student Activities ──────────────────────────────────────────────
        activity_synced = 0
        for doc in fs.collection("student_activities").stream():
            data = doc.to_dict() or {}
            try:
                raw_json = json.dumps(data)
                cur.execute(
                    """INSERT OR REPLACE INTO student_activities
                       (activity_id, student_id, activity_type, title,
                        xp_earned, description, raw_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        doc.id,
                        data.get("student_id", ""),
                        data.get("activity_type", ""),
                        data.get("title", ""),
                        data.get("xp_earned", 0),
                        data.get("description", ""),
                        raw_json,
                    ),
                )
                activity_synced += 1
            except Exception as e:
                current_app.logger.warning(f"student_activity {doc.id} skipped: {e}")

        db.commit()
        cache_clear()  # invalidate caches after successful sync
        return jsonify({
            "success": True,
            "message": (
                f"Synced {users_synced} users, {attendance_synced} attendance, "
                f"{quiz_synced} quiz attempts, {activity_synced} activities."
            ),
            "users": users_synced,
            "attendance": attendance_synced,
            "quiz_attempts": quiz_synced,
            "activities": activity_synced,
            "completed_at": datetime.now().isoformat(),
        })
    except Exception as e:
        current_app.logger.error(f"Firebase sync failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/status")
def status():
    """Quick reachability check — does firebase_admin import & a Firestore client init."""
    try:
        _firestore_client()
        return jsonify({"success": True, "firebase": "reachable"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
