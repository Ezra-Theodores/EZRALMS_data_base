"""
Phase 2 migration: build ezralms_unified.db from the three existing SQLite DBs.

Strategy
--------
* Originals stay untouched (copied to backups/ first for safety).
* Canonical base = data_house.db (35 MB, Firebase-synced, real production data:
  93 users, 400 quizzes, 7,770 questions, 845 quiz_attempts, etc.)
* From ezralms.db pull the 5 tables that don't exist in data_house:
      grades, sub_topics, materials, quiz_questions      (curriculum seed data)
  ezralms.db is used because it has `grades` while ezralms_complete.db does not;
  all other tables in the two small DBs are equivalent.
* Collision tables (users, classes, topics, quizzes) keep the data_house version
  and the small-DB copies are imported with a `legacy_` prefix so no data is
  lost. Curriculum tree queries will use the legacy_* tables; analytics use the
  rich versions.

Idempotent: re-running drops and rebuilds ezralms_unified.db from scratch.

Usage:
    py -3 migrate_to_unified_db.py
    py -3 migrate_to_unified_db.py --dry-run
"""

import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DATA_HOUSE = os.path.join(ROOT, "data_house.db")
SRC_COMPLETE = os.path.join(ROOT, "ezralms_complete.db")
SRC_SMALL = os.path.join(ROOT, "ezralms.db")   # has the curriculum seed incl. grades
TARGET = os.path.join(ROOT, "ezralms_unified.db")
BACKUP_DIR = os.path.join(ROOT, "backups")

# Tables to bring across with rename (collision tables from ezralms_complete.db).
LEGACY_RENAMES = {
    "users": "legacy_users",
    "classes": "legacy_classes",
    "topics": "legacy_topics",
    "quizzes": "legacy_quizzes",
}

# Tables to bring across unchanged (unique to the small curriculum DB).
COMPLETE_UNIQUE_TABLES = ["grades", "sub_topics", "materials", "quiz_questions"]


def backup_originals(dry_run: bool) -> None:
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for src in (SRC_DATA_HOUSE, SRC_COMPLETE, SRC_SMALL):
        if not os.path.exists(src):
            print(f"  [skip] {src} not found")
            continue
        dst = os.path.join(BACKUP_DIR, f"{os.path.basename(src)}.{ts}.bak")
        size_mb = os.path.getsize(src) / (1024 * 1024)
        if dry_run:
            print(f"  [dry-run] would copy {src} -> {dst} ({size_mb:.1f} MB)")
        else:
            shutil.copy2(src, dst)
            print(f"  [ok] {os.path.basename(src)} -> {os.path.basename(dst)} ({size_mb:.1f} MB)")


def copy_base(dry_run: bool) -> None:
    """Copy data_house.db to ezralms_unified.db (the canonical base)."""
    size_mb = os.path.getsize(SRC_DATA_HOUSE) / (1024 * 1024)
    if dry_run:
        print(f"  [dry-run] would copy {SRC_DATA_HOUSE} -> {TARGET} ({size_mb:.1f} MB)")
        return
    if os.path.exists(TARGET):
        os.remove(TARGET)
        print(f"  [reset] removed existing {os.path.basename(TARGET)}")
    shutil.copy2(SRC_DATA_HOUSE, TARGET)
    print(f"  [ok] base = {os.path.basename(SRC_DATA_HOUSE)} -> {os.path.basename(TARGET)} ({size_mb:.1f} MB)")


def _table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name = ?",
        (table,),
    )
    return cur.fetchone() is not None


def _build_create_from_pragma(cur: sqlite3.Cursor, source_alias: str,
                              source_table: str, target_table: str) -> str:
    """Reconstruct a CREATE TABLE statement from PRAGMA table_info when sqlite_master.sql is NULL."""
    cur.execute(f'PRAGMA {source_alias}.table_info("{source_table}")')
    cols = cur.fetchall()
    if not cols:
        raise RuntimeError(f"{source_table}: PRAGMA table_info empty in {source_alias}")
    parts = []
    pk_cols = []
    for cid, name, ctype, notnull, dflt, pk in cols:
        col = f'"{name}" {ctype or "TEXT"}'
        if notnull:
            col += " NOT NULL"
        if dflt is not None:
            col += f" DEFAULT {dflt}"
        if pk and len([c for c in cols if c[5]]) == 1:
            col += " PRIMARY KEY"
        else:
            if pk:
                pk_cols.append(name)
        parts.append(col)
    if pk_cols:
        parts.append('PRIMARY KEY (' + ', '.join(f'"{c}"' for c in pk_cols) + ')')
    return f'CREATE TABLE "{target_table}" (\n  ' + ',\n  '.join(parts) + '\n)'


def _copy_table(target_conn: sqlite3.Connection, source_alias: str,
                source_table: str, target_table: str) -> int:
    """Copy a single table from an attached DB into the target connection.

    Falls back to PRAGMA-based CREATE if sqlite_master.sql is NULL or rewriting
    the identifier fails.
    """
    import re
    cur = target_conn.cursor()
    # CRITICAL: schema-qualify the DROP. Without "main.", SQLite falls back
    # to attached DBs when the table is missing from main — which would
    # destroy the source.
    cur.execute(f'DROP TABLE IF EXISTS main."{target_table}"')

    # Try sqlite_master first
    cur.execute(
        f"SELECT sql FROM {source_alias}.sqlite_master "
        "WHERE type='table' AND name = ?",
        (source_table,),
    )
    row = cur.fetchone()

    if row and row[0]:
        create_sql = row[0]
        create_sql_renamed = re.sub(
            r'(CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?)["`]?' + re.escape(source_table) + r'["`]?',
            rf'\1"{target_table}"',
            create_sql,
            count=1,
            flags=re.IGNORECASE,
        )
        if target_table not in create_sql_renamed:
            # Last-resort: rebuild from PRAGMA
            create_sql_renamed = _build_create_from_pragma(cur, source_alias, source_table, target_table)
    else:
        # Reconstruct from PRAGMA table_info
        create_sql_renamed = _build_create_from_pragma(cur, source_alias, source_table, target_table)

    # Force CREATE into main.* by injecting the qualifier if absent.
    create_sql_renamed = re.sub(
        r'(CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?)(?!main\.)',
        r'\1main.',
        create_sql_renamed,
        count=1,
        flags=re.IGNORECASE,
    )
    cur.execute(create_sql_renamed)
    cur.execute(f'INSERT INTO main."{target_table}" SELECT * FROM {source_alias}."{source_table}"')
    cur.execute(f'SELECT COUNT(*) FROM main."{target_table}"')
    return cur.fetchone()[0]


def migrate_complete_tables(dry_run: bool) -> None:
    """Pull grades, sub_topics, materials, quiz_questions, and legacy_* tables in."""
    if dry_run:
        print(f"  [dry-run] would attach {os.path.basename(SRC_SMALL)} and copy:")
        for t in COMPLETE_UNIQUE_TABLES:
            print(f"             {t}")
        for src, dst in LEGACY_RENAMES.items():
            print(f"             {src} -> {dst}")
        return

    conn = sqlite3.connect(TARGET)
    try:
        conn.execute(f"ATTACH DATABASE '{SRC_SMALL}' AS src")
        # Unique tables (curriculum seed data)
        for t in COMPLETE_UNIQUE_TABLES:
            src_cur = conn.execute(
                "SELECT name FROM src.sqlite_master WHERE type='table' AND name = ?", (t,)
            ).fetchone()
            if not src_cur:
                print(f"  [skip] {t} not present in {os.path.basename(SRC_SMALL)}")
                continue
            count = _copy_table(conn, "src", t, t)
            print(f"  [ok] {t}  ({count} rows)")

        # Collision tables (rename to legacy_*)
        for src_name, dst_name in LEGACY_RENAMES.items():
            src_cur = conn.execute(
                "SELECT name FROM src.sqlite_master WHERE type='table' AND name = ?", (src_name,)
            ).fetchone()
            if not src_cur:
                print(f"  [skip] {src_name} not present in {os.path.basename(SRC_SMALL)}")
                continue
            count = _copy_table(conn, "src", src_name, dst_name)
            print(f"  [ok] {src_name} -> {dst_name}  ({count} rows)")

        conn.commit()
    finally:
        try:
            conn.execute("DETACH DATABASE src")
        except sqlite3.OperationalError:
            pass
        conn.close()


def verify(dry_run: bool) -> None:
    if dry_run:
        print("  [dry-run] skipping verification")
        return
    conn = sqlite3.connect(TARGET)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    print(f"  unified DB has {len(tables)} tables:")
    for t in tables:
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{t}"')
            n = cur.fetchone()[0]
        except sqlite3.OperationalError as e:
            n = f"ERR:{e}"
        flag = ""
        if t in COMPLETE_UNIQUE_TABLES:
            flag = "  (curriculum seed)"
        elif t in LEGACY_RENAMES.values():
            flag = "  (legacy seed)"
        print(f"    {t:35s} {n:>8} rows{flag}")
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print plan without changing disk")
    args = parser.parse_args()

    dry = args.dry_run
    print("=" * 60)
    print(f"EZRA LMS unified DB migration {'(dry run)' if dry else ''}")
    print("=" * 60)
    print("\n[1/4] Backing up originals to ./backups/")
    backup_originals(dry)
    print("\n[2/4] Copying data_house.db -> ezralms_unified.db")
    copy_base(dry)
    print(f"\n[3/4] Importing curriculum seed + legacy tables from {os.path.basename(SRC_SMALL)}")
    migrate_complete_tables(dry)
    print("\n[4/4] Verifying unified DB")
    verify(dry)
    print("\nDone." + ("  (no changes made)" if dry else f"  Target: {TARGET}"))


if __name__ == "__main__":
    main()
