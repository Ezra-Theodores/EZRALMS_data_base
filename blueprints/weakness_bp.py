"""
/api/weakness/*  -  Weak-spot analysis from quiz_attempts.

Phase 2 update: the unified DB has 845 quiz_attempts with columns student_id /
quiz_id / score / max_score / completed_at (snake_case). The data_house
quizzes table has no topic_id, so we aggregate weakness by `subject` (which
quizzes carry) and recommend other quizzes in weak subjects that the student
has not already passed.
"""

from flask import Blueprint, jsonify, current_app

from ._db import get_unified_db, close_all

bp = Blueprint("weakness", __name__, url_prefix="/api/weakness")
bp.teardown_request(close_all)


@bp.route("/ping")
def ping():
    return jsonify({"success": True, "blueprint": "weakness"})


@bp.route("/student/<student_id>")
def get_weaknesses_and_recommendations(student_id):
    """Weak subjects (<70% mastery on most-recent attempts) + recommended quizzes."""
    try:
        cur = get_unified_db().cursor()

        mastery_query = """
        WITH LatestAttempts AS (
            SELECT
                student_id, quiz_id, score, max_score,
                (CAST(score AS REAL) / NULLIF(CAST(max_score AS REAL), 0)) * 100 AS percentage,
                ROW_NUMBER() OVER (PARTITION BY student_id, quiz_id ORDER BY completed_at DESC) AS rn
            FROM quiz_attempts
            WHERE student_id = ?
        )
        SELECT
            COALESCE(q.subject, 'Unknown') AS subject,
            AVG(la.percentage) AS average_score,
            COUNT(la.quiz_id) AS quizzes_attempted
        FROM LatestAttempts la
        JOIN quizzes q ON la.quiz_id = q.quiz_id
        WHERE la.rn = 1
        GROUP BY subject
        HAVING average_score < 70.0
        ORDER BY average_score ASC
        """
        cur.execute(mastery_query, (student_id,))
        weak_subjects = cur.fetchall()

        weaknesses, recommendations = [], []
        rec_query = """
        SELECT q.quiz_id, q.title AS quiz_title, q.subject, q.grade, q.difficulty
        FROM quizzes q
        WHERE q.subject = ?
          AND q.quiz_id NOT IN (
              SELECT quiz_id FROM quiz_attempts
              WHERE student_id = ?
                AND (CAST(score AS REAL) / NULLIF(CAST(max_score AS REAL), 0)) >= 0.7
          )
        LIMIT ?
        """
        for row in weak_subjects:
            weaknesses.append({
                "subject": row["subject"],
                "average_score": round(row["average_score"], 2),
                "quizzes_attempted": row["quizzes_attempted"],
            })
            remaining = 5 - len(recommendations)
            if remaining > 0:
                cur.execute(rec_query, (row["subject"], student_id, remaining))
                for rec in cur.fetchall():
                    recommendations.append({
                        "quiz_id": rec["quiz_id"],
                        "quiz_title": rec["quiz_title"],
                        "subject": rec["subject"],
                        "grade": rec["grade"],
                        "difficulty": rec["difficulty"],
                    })

        return jsonify({
            "success": True,
            "student_id": student_id,
            "weaknesses": weaknesses,
            "recommendations": recommendations,
        })
    except Exception as e:
        current_app.logger.error(f"Weakness lookup failed for {student_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/leaderboard")
def leaderboard():
    """Top 20 students by total XP (joined with users table)."""
    try:
        cur = get_unified_db().cursor()
        cur.execute(
            """SELECT u.user_id, u.name, u.role, u.xp,
                      (SELECT COUNT(*) FROM quiz_attempts qa WHERE qa.student_id = u.user_id) AS attempts
               FROM users u
               WHERE u.role = 'student'
               ORDER BY COALESCE(u.xp, 0) DESC
               LIMIT 20"""
        )
        return jsonify({"success": True, "data": [dict(r) for r in cur.fetchall()]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
