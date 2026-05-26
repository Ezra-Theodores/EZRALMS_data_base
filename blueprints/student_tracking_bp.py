"""
/api/students/*  -  Student Tracking

Full student profile including:
- Student search by name
- Quiz attempts with per-quiz scores and details
- Attendance summary for the last 30 days
- Materials opened count
- Tasks/assignments with status
- XP history
- Topic mastery grouped by math category:
  Bilangan (Number Theory), Aljabar (Algebra), Data (Statistics),
  Geometri (Geometry), Kombinatorik (Combinatorics), Logika (Logic)
"""

import hashlib
import json
import re

from flask import Blueprint, jsonify, request, current_app
from ._cache import (
    LeaderboardCache,
    ProfileCache,
    _stats_lock,
    cache_stats,
)
from ._db import get_unified_db, close_all

bp = Blueprint("students", __name__, url_prefix="/api/students")
bp.teardown_request(close_all)

# ── ETag helpers ────────────────────────────────────────────────────────────────


def _make_etag(data):
    """MD5 hexdigest of serialized JSON — cheap, stable."""
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _etag_response(data, response):
    """Compute ETag and attach Cache-Control + ETag headers; handle 304."""
    etag = _make_etag(data)
    # Check If-None-Match
    inm = request.headers.get("If-None-Match")
    if inm and inm == etag:
        response.status_code = 304
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=300"
        return response
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=300"
    return response

# ── Topic-category mapping ──────────────────────────────────────────────────
# Maps keywords in topic/quiz titles to math categories.
_CATEGORY_RULES = [
    ("Bilangan",  ["bilangan", "number", "angka", "prima", "faktor", "kelipatan", "ganjil", "genap", "mod", "divisibility", "multiples", "factors", "primes"]),
    ("Aljabar",   ["aljabar", "algebra", "persamaan", "fungsi", "kuadrat", "linear", "variabel", "ekspresi", "polynomial", "variable", "equation", "quadratic", "inequality", "system", "matriks", "matrix", "determinan", "determinant", "logaritma", "logarithm", "eksponen", "exponent", "barisan", "sequence", "deret", "series", "limit", " diferensial", "calculus", "ratio", "proportion", "percent", "percentage"]),
    ("Data",     ["data", "statistik", "statistic", "probabilitas", "probability", "peluang", "chance", "diagram", "chart", "grafik", "graph", "mean", "median", "modus", "range", "variansi", "variance", "survey", "pengumpulan data"]),
    ("Geometri",  ["geometri", "geometry", "bangun", "ruang", "lingkaran", "segitiga", "persegi", "角度", "angle", "luas", "keliling", "volume", "simetri", "symmetry", "transformasi", "transformation", "kongruen", "congruent", "sebangun", "similar", "phythagoras", "pythagoras", "koordinat", "coordinate", "kerucut", "bola", "prisma", "limas", "tabung", "balok", "kubus"]),
    ("Kombinatorik", ["kombinatorik", "combinatorics", "kombinasi", "permutasi", "permutation", "combination", "arrangement", "pigeonhole", "dasar menghitung"]),
    ("Logika",    ["logika", "logic", " penalaran", "reasoning", "pola", "pattern", "urutan", "sequence", "berpikir kritis", "critical thinking", "analisis"]),
]

def _categorize(text: str) -> str:
    """Return math category based on keyword matching."""
    t = text.lower()
    for category, keywords in _CATEGORY_RULES:
        for kw in keywords:
            if kw in t:
                return category
    return "Lainnya"


# ── Helpers ─────────────────────────────────────────────────────────────────

def _grade_from_quiz_title(title: str) -> str:
    """Extract grade number from quiz title like 'G7-01.2 Multiples, factors…'."""
    m = re.search(r'G(\d+)', title or '')
    return m.group(1) if m else ''

def _score_pct(score, max_score):
    try:
        s, m = float(score), float(max_score)
        return round(s / m * 100, 1) if m else 0
    except:
        return 0


# ── Routes ──────────────────────────────────────────────────────────────────

@bp.route("/ping")
def ping():
    return jsonify({"success": True, "blueprint": "students"})


@bp.route("/search")
def search():
    """Search students by name (from users + student_activities + quiz_attempts)."""
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"success": False, "error": "Missing 'q' parameter"}), 400

    try:
        cur = get_unified_db().cursor()
        pattern = f"%{q}%"

        # Collect distinct student IDs from quiz_attempts raw_json + student_activities
        cur.execute("""
            SELECT DISTINCT student_id
            FROM (
                SELECT json_extract(raw_json, '$.userId') AS student_id
                FROM quiz_attempts
                WHERE raw_json IS NOT NULL AND student_id IS NULL
                UNION
                SELECT student_id FROM student_activities
                WHERE student_id IS NOT NULL AND student_id != ''
            )
            WHERE student_id IS NOT NULL AND student_id != ''
        """)
        candidate_ids = [r["student_id"] for r in cur.fetchall()]

        # Fetch ALL students — filter and limit in Python so no match is missed
        cur.execute("""
            SELECT id, user_id, name, email, role, xp, avatar_url, raw_json
            FROM users
            WHERE role IN ('student','tutor')
              AND (name IS NOT NULL AND name != ''
                   OR raw_json LIKE '%"displayName"%')
            ORDER BY id
        """)
        users = []
        for row in cur.fetchall():
            u = dict(row)
            # Extract various name variants from raw_json when name column is empty
            if u.get("raw_json"):
                try:
                    d = json.loads(u["raw_json"])
                    u["profile_displayName"] = d.get("displayName") or ""
                    u["student_username"] = (
                        d.get("studentDetails", {}).get("username") or ""
                    )
                    u["profile_firstName"] = (
                        d.get("profile", {}).get("firstName") or ""
                    )
                    u["profile_lastName"] = (
                        d.get("profile", {}).get("lastName") or ""
                    )
                    # Use profile.displayName as primary name when column is empty
                    if not u.get("name"):
                        u["name"] = (
                            u["profile_displayName"]
                            or f"{u['profile_firstName']} {u['profile_lastName']}".strip()
                            or u["student_username"]
                            or ""
                        )
                except:
                    pass
            # Prefer Firebase uid from raw_json.uid, fall back to _id_N
            raw = u.get("raw_json") or "{}"
            try:
                raw_d = json.loads(raw)
            except:
                raw_d = {}
            u["user_id"] = raw_d.get("uid") or u.get("user_id") or f"_id_{u['id']}"
            users.append(u)

        def matches(u, q):
            q = q.lower()
            return (
                q in (u.get("name") or "").lower()
                or q in (u.get("email") or "").lower()
                or q in (u.get("user_id") or "").lower()
                or q in (u.get("profile_displayName") or "").lower()
                or q in (u.get("student_username") or "").lower()
                or q in (u.get("profile_firstName") or "").lower()
                or q in (u.get("profile_lastName") or "").lower()
            )

        users = [u for u in users if matches(u, q)][:50]

        # Enrich with last-active from quiz_attempts
        for u in users:
            uid = u["user_id"]
            if uid.startswith("_id_"):
                continue
            cur.execute("""
                SELECT completed_at FROM quiz_attempts
                WHERE json_extract(raw_json, '$.userId') = ?
                ORDER BY completed_at DESC LIMIT 1
            """, (uid,))
            row = cur.fetchone()
            u["last_active"] = row["completed_at"] if row else None

        return jsonify({"success": True, "count": len(users), "data": users})
    except Exception as e:
        current_app.logger.error(f"Student search failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/profile/<student_id>")
def profile(student_id):
    """
    Full student profile:
      - Basic info (name, email, xp, avatar)
      - Quiz summary (total, average score, attempts)
      - Attendance last 30 days
      - Materials opened (via student_activities subtopic_completed)
      - XP history
      - Topic mastery by math category
      - Task assignments
    """
    # ── Cache hit path ────────────────────────────────────────────────────────
    cached = ProfileCache.get(student_id)
    if cached is not None:
        with _stats_lock:
            cache_stats().profile_hits += 1
        resp = jsonify(cached)
        return _etag_response(cached, resp)

    with _stats_lock:
        cache_stats().profile_misses += 1

    try:
        cur = get_unified_db().cursor()

        # ── Basic info ────────────────────────────────────────────────────
        # Support lookup by:
        #   1. Firebase uid stored as user_id column
        #   2. Firebase uid embedded in raw_json
        #   3. _id_N  → users.id = N  (for students with NULL user_id)
        #   4. Numeric id directly
        row = None

        # Try direct user_id
        cur.execute("""
            SELECT id, user_id, name, email, role, xp, avatar_url, raw_json
            FROM users WHERE user_id = ?
        """, (student_id,))
        row = cur.fetchone()

        if not row:
            # Try Firebase uid in raw_json
            cur.execute("""
                SELECT id, user_id, name, email, role, xp, avatar_url, raw_json
                FROM users WHERE raw_json LIKE ?
                LIMIT 1
            """, (f'%"{student_id}"%',))
            row = cur.fetchone()

        if not row:
            # Try _id_N  → users.id = N
            if student_id.startswith("_id_"):
                numeric_id = student_id[4:]
                cur.execute("""
                    SELECT id, user_id, name, email, role, xp, avatar_url, raw_json
                    FROM users WHERE id = ?
                """, (numeric_id,))
                row = cur.fetchone()

        if not row:
            # Try plain numeric id
            cur.execute("""
                SELECT id, user_id, name, email, role, xp, avatar_url, raw_json
                FROM users WHERE id = ?
            """, (student_id,))
            row = cur.fetchone()

        if not row:
            return jsonify({"success": False, "error": "Student not found"}), 404

        info = dict(row)
        # Parse name from raw_json if column is empty — try all name variants
        if info.get("raw_json"):
            try:
                d = json.loads(info["raw_json"])
                info["name"] = (
                    d.get("displayName")
                    or f"{d.get('profile',{}).get('firstName','')} {d.get('profile',{}).get('lastName','')}".strip()
                    or d.get("studentDetails", {}).get("username")
                    or d.get("normalizedName")
                    or info.get("name") or ""
                )
            except:
                pass

        raw = info.get("raw_json") or "{}"
        try:
            raw_d = json.loads(raw)
        except:
            raw_d = {}
        real_uid = raw_d.get("uid") or info.get("user_id") or f"_id_{info['id']}"
        info.pop("raw_json", None)

        # ── Quiz attempts (from raw_json userId field) ────────────────────
        cur.execute("""
            SELECT id, quiz_id, score, max_score, completed_at, raw_json
            FROM quiz_attempts
            WHERE json_extract(raw_json, '$.userId') = ?
            ORDER BY completed_at DESC
        """, (real_uid,))
        attempts_raw = cur.fetchall()

        quizzes = []
        topic_stats = {}   # topic -> {total, scores[], avg}
        category_scores = {}

        for a in attempts_raw:
            raw = json.loads(a["raw_json"]) if a["raw_json"] else {}
            quiz_title = raw.get("quizTitle", a["quiz_id"])
            pct = _score_pct(a["score"], a["max_score"])
            grade = _grade_from_quiz_title(quiz_title)
            category = _categorize(quiz_title)

            quizzes.append({
                "quiz_id":      a["quiz_id"],
                "quiz_title":   quiz_title,
                "score":        a["score"],
                "max_score":    a["max_score"],
                "percentage":   pct,
                "completed_at": a["completed_at"],
                "grade":        grade,
                "category":     category,
                "passed":       pct >= 60,
            })

            # Accumulate per-topic
            topic_key = raw.get("topic", quiz_title)
            if topic_key not in topic_stats:
                topic_stats[topic_key] = {"scores": [], "quiz_titles": []}
            topic_stats[topic_key]["scores"].append(pct)
            topic_stats[topic_key]["quiz_titles"].append(quiz_title)

            # Accumulate per-category
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(pct)

        # Build topic mastery
        topic_mastery = []
        for topic, data in topic_stats.items():
            scores = data["scores"]
            topic_mastery.append({
                "topic":       topic,
                "attempts":    len(scores),
                "average":     round(sum(scores) / len(scores), 1),
                "latest":      scores[0],
                "trend":       "up" if scores[-1] > scores[0] else "down",
            })
        topic_mastery.sort(key=lambda x: x["average"])

        # Build category summary
        categories = []
        for cat, scores in category_scores.items():
            categories.append({
                "name":     cat,
                "attempts": len(scores),
                "average":  round(sum(scores) / len(scores), 1),
            })
        categories.sort(key=lambda x: x["average"])

        # Quiz summary
        total_quizzes = len(quizzes)
        avg_score = round(sum(q["percentage"] for q in quizzes) / total_quizzes, 1) if total_quizzes else 0

        # ── Attendance (last 30 days) ──────────────────────────────────────
        cur.execute("""
            SELECT attendance_date, status, check_in_time
            FROM attendance
            WHERE student_id = ?
              AND attendance_date IS NOT NULL AND attendance_date != ''
            ORDER BY attendance_date DESC
            LIMIT 30
        """, (student_id,))
        attendance_rows = cur.fetchall()
        attendance = [dict(r) for r in attendance_rows]

        # Summarize attendance
        present = sum(1 for a in attendance if a["status"] in ("present", "hadir", "checked_in"))
        absent  = sum(1 for a in attendance if a["status"] in ("absent", "alfa"))
        late    = sum(1 for a in attendance if a["status"] in ("late", "terlambat"))
        total_days = len(attendance)
        attendance_rate = round(present / total_days * 100, 1) if total_days else 0

        # ── Materials opened (student_activities) ─────────────────────────
        cur.execute("""
            SELECT id, activity_type, raw_json, created_at
            FROM student_activities
            WHERE student_id = ?
            ORDER BY created_at DESC
        """, (student_id,))
        activities = [dict(r) for r in cur.fetchall()]

        materials_opened = sum(
            1 for a in activities
            if a["activity_type"] in ("subtopic_completed", "material_opened", "material_viewed")
        )

        # ── XP history ───────────────────────────────────────────────────
        cur.execute("""
            SELECT id, raw_json, created_at
            FROM xp_transactions
            WHERE json_extract(raw_json, '$.studentId') = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (student_id,))
        xp_rows = cur.fetchall()
        xp_history = []
        for xp in xp_rows:
            raw = json.loads(xp["raw_json"]) if xp["raw_json"] else {}
            xp_history.append({
                "amount":   raw.get("xpAwarded", 0),
                "sourceId": raw.get("sourceId", ""),
                "at":       raw.get("timestamp", xp["created_at"]),
            })

        total_xp = sum(x["amount"] for x in xp_history)

        # ── Task assignments ─────────────────────────────────────────────
        cur.execute("""
            SELECT id, raw_json, created_at
            FROM task_assignments
            WHERE student_id = ?
            ORDER BY created_at DESC
            LIMIT 30
        """, (student_id,))
        task_rows = cur.fetchall()
        tasks = []
        for t in task_rows:
            raw = json.loads(t["raw_json"]) if t["raw_json"] else {}
            tasks.append({
                "title":       raw.get("taskTitle", ""),
                "description":  raw.get("taskDescription", ""),
                "quiz_title":  raw.get("quizTitle", ""),
                "status":      raw.get("status", "pending"),
                "due_date":    raw.get("dueDate", ""),
                "completed_at": raw.get("completedAt", ""),
            })

        resp = jsonify({
            "success": True,
            "student": {
                **info,
                "total_xp":      total_xp,
                "xp_history":    xp_history,
            },
            "quiz_summary": {
                "total":       total_quizzes,
                "average":     avg_score,
                "attempts":    len(attempts_raw),
            },
            "quizzes": quizzes,
            "attendance": {
                "summary": {
                    "total_days":      total_days,
                    "present":         present,
                    "absent":          absent,
                    "late":            late,
                    "attendance_rate": attendance_rate,
                },
                "records": attendance,
            },
            "materials_opened": materials_opened,
            "activities": activities,
            "tasks": tasks,
            "topic_mastery": topic_mastery,
            "categories": categories,
        })
        # Cache result then apply ETag/Cache-Control headers
        result_data = resp.get_json()
        ProfileCache[student_id] = result_data
        return _etag_response(result_data, resp)
    except Exception as e:
        current_app.logger.error(f"Student profile failed for {student_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/leaderboard")
def leaderboard():
    """Top 20 students by XP (from xp_transactions + users table)."""
    # ── Leaderboard cache ──────────────────────────────────────────────────────
    cached = LeaderboardCache.get("leaderboard")
    if cached is not None:
        with _stats_lock:
            cache_stats().leaderboard_hits += 1
        resp = jsonify(cached)
        return _etag_response(cached, resp)

    with _stats_lock:
        cache_stats().leaderboard_misses += 1

    try:
        cur = get_unified_db().cursor()
        cur.execute("""
            SELECT
                u.user_id,
                u.name,
                COALESCE(u.xp,
                    (SELECT SUM(json_extract(raw_json, '$.xpAwarded'))
                     FROM xp_transactions
                     WHERE json_extract(raw_json, '$.studentId') = u.user_id)
                ) AS total_xp,
                (SELECT COUNT(*) FROM quiz_attempts
                 WHERE json_extract(raw_json, '$.userId') = u.user_id) AS quiz_count
            FROM users u
            WHERE u.role IN ('student','tutor')
              AND u.name IS NOT NULL AND u.name != ''
            ORDER BY total_xp DESC NULLS LAST
            LIMIT 20
        """)
        data = {"success": True, "data": [dict(r) for r in cur.fetchall()]}
        LeaderboardCache["leaderboard"] = data
        resp = jsonify(data)
        return _etag_response(data, resp)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500