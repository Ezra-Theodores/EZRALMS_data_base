"""
Shared SQLite helper — Phase 2 single source of truth.

All blueprints connect to ezralms_unified.db (built by migrate_to_unified_db.py).
The three legacy paths still work as fallbacks for emergency rollback: set
UNIFIED_DB=ezralms.db (etc.) to revert temporarily.

Schema highlights:
  * users / classes / topics / quizzes / questions / attendance ... from Firebase
    sync (rich, 7,770 questions, 400 quizzes, 93 users, etc.)
  * grades / sub_topics / materials / quiz_questions ......... curriculum seed
  * legacy_users / legacy_classes / legacy_topics / legacy_quizzes ...
    sample-data seed kept for the curriculum tree view
"""

import os
import sqlite3
from flask import g

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UNIFIED_DB = os.getenv("UNIFIED_DB", os.path.join(ROOT, "ezralms_unified.db"))


def _get(path: str, key: str):
    if key not in g:
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        setattr(g, key, conn)
    return getattr(g, key)


def get_unified_db():
    """Canonical connection — use this in new code."""
    return _get(UNIFIED_DB, "_unified_db")


# Backwards-compatible aliases so the existing blueprint imports keep working.
def get_attendance_db():
    return get_unified_db()


def get_complete_db():
    return get_unified_db()


def get_data_house_db():
    return get_unified_db()


def close_all(exception=None):
    for key in ("_unified_db", "_attendance_db", "_complete_db", "_data_house_db"):
        conn = g.pop(key, None)
        if conn is not None:
            conn.close()
