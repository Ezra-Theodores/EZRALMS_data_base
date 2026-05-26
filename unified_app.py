"""
EZRA LMS - Unified Web UI (Phase 1 scaffold)
============================================
Single Flask app that mounts every existing module as a namespaced blueprint:

    /api/attendance/*    -> from app.py
    /api/curriculum/*    -> from app_complete.py (users, tree, CRUD)
    /api/weakness/*      -> from app_complete.py (recommendations)
    /api/automation/*    -> from app_complete.py (Node.js automation hub)
    /api/sync/*          -> Firebase Firestore sync
    /api/pipeline/*      -> from DATA_HOUSE_EZRALMS/server_v2.py
    /api/rag/*           -> from data_house.py (BM25 search)
    /api/quizzes/*       -> backend for the orphan RAG UI

Existing apps (app.py, app_complete.py, server.py, server_v2.py) are NOT
modified. Run them as before, or run this scaffold instead.

Usage:
    python unified_app.py
    -> http://localhost:5000
"""

import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

from blueprints.attendance_bp import bp as attendance_bp
from blueprints.cache_stats_bp import bp as cache_stats_bp
from blueprints.curriculum_bp import bp as curriculum_bp
from blueprints.student_tracking_bp import bp as student_tracking_bp
from blueprints.weakness_bp import bp as weakness_bp
from blueprints.automation_bp import bp as automation_bp
from blueprints.firebase_sync_bp import bp as firebase_sync_bp
from blueprints.pipeline_bp import bp as pipeline_bp
from blueprints.rag_bp import bp as rag_bp
from blueprints.quiz_manager_bp import bp as quiz_manager_bp
from blueprints.finance import finance_bp

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"] = os.urandom(24)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB for pipeline uploads

# Register all blueprints
BLUEPRINTS = [
    attendance_bp,
    cache_stats_bp,
    curriculum_bp,
    student_tracking_bp,
    weakness_bp,
    automation_bp,
    firebase_sync_bp,
    pipeline_bp,
    rag_bp,
    quiz_manager_bp,
    finance_bp,
]
for bp in BLUEPRINTS:
    app.register_blueprint(bp)


@app.route("/")
def index():
    """Unified SPA — single-page front-end for every blueprint."""
    return render_template("unified_spa.html")


@app.route("/_namespaces")
def namespaces():
    """Diagnostic landing page (the old Phase 1 listing)."""
    return render_template("unified_index.html", blueprints=[
        {"name": bp.name, "prefix": bp.url_prefix, "ping": f"{bp.url_prefix}/ping"}
        for bp in BLUEPRINTS
    ])


@app.route("/api/ping")
def ping():
    """Root health-check."""
    return jsonify({
        "success": True,
        "service": "ezralms-unified",
        "blueprints": [bp.name for bp in BLUEPRINTS],
    })


if __name__ == "__main__":
    port = int(os.getenv("UNIFIED_PORT", "5000"))
    print("=" * 60)
    print("EZRA LMS - Unified Web UI (Phase 1 scaffold)")
    print("=" * 60)
    for bp in BLUEPRINTS:
        print(f"  {bp.url_prefix:<24} -> {bp.name}")
    print("=" * 60)
    print(f"Open browser to: http://localhost:{port}")
    print("Press CTRL+C to stop\n")
    app.run(host="0.0.0.0", port=port, debug=True)
