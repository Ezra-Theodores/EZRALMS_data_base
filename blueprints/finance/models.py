"""
Finance data models.
Reads from finance_transactions table in ezralms_unified.db.
Creates the table if it doesn't exist (schema is auto-initialized).
"""
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

# Use DATABASE_PATH env first (for Railway/production), else
# DB_PATH for local dev convenience. Defaults to ezralms_unified.db
# in the project root so tests and dev servers all hit the same file.
DB_PATH = os.environ.get("DATABASE_PATH") or os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                 "ezralms_unified.db")
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS finance_transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id       TEXT    UNIQUE NOT NULL,
    date        TEXT    NOT NULL,   -- ISO format: YYYY-MM-DD
    category    TEXT    NOT NULL,   -- 'income' or 'expense'
    type_       TEXT    NOT NULL,   -- e.g. 'package_sale', 'refund', 'salary', 'software', 'marketing'
    amount      REAL    NOT NULL,
    description TEXT,
    reference   TEXT,
    created_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ft_date      ON finance_transactions(date);
CREATE INDEX IF NOT EXISTS idx_ft_category  ON finance_transactions(category);

-- Student Tuition system
CREATE TABLE IF NOT EXISTS student_tuition (
    student_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    grade        INTEGER,
    school       TEXT,
    monthly_amount INTEGER NOT NULL,
    status       TEXT DEFAULT 'active',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tuition_payments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id   TEXT NOT NULL,
    month        TEXT NOT NULL,
    payment_date TEXT,
    amount_paid  INTEGER DEFAULT 0,
    notes        TEXT,
    created_at   TEXT NOT NULL,
    FOREIGN KEY (student_id) REFERENCES student_tuition(student_id)
);

CREATE INDEX IF NOT EXISTS idx_tp_student ON tuition_payments(student_id);
CREATE INDEX IF NOT EXISTS idx_tp_month  ON tuition_payments(month);
"""


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)  # runs multi-statement DDL safely
    conn.commit()
    return conn


def get_all_transactions(
    start_date: Optional[str] = None,
    end_date:   Optional[str] = None,
    category:    Optional[str] = None,
) -> list[dict]:
    conn = _get_conn()
    query = "SELECT id, tx_id, date, category, type_, amount, description, reference, created_at FROM finance_transactions WHERE 1=1"
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [
        {
            "id":          r[0],
            "tx_id":       r[1],
            "date":        r[2],
            "category":    r[3],
            "type":        r[4],
            "amount":      r[5],
            "description": r[6],
            "reference":   r[7],
            "created_at":  r[8],
        }
        for r in rows
    ]


def get_summary(start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict:
    conn = _get_conn()
    def total(cat):
        row = conn.execute(
            f"SELECT COALESCE(SUM(amount),0) FROM finance_transactions WHERE category=? AND date >= COALESCE(?, date) AND date <= COALESCE(?, date)",
            [cat, start_date, end_date]
        ).fetchone()
        return row[0] if row else 0.0

    income   = total("income")
    expenses = total("expense")
    return {
        "total_income":   income,
        "total_expenses": expenses,
        "net_profit":     income - expenses,
        "currency":       "IDR",
    }


def get_monthly_breakdown(year: int) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute("""
        SELECT
            strftime('%m', date)       AS month,
            category,
            SUM(amount)                AS total
        FROM finance_transactions
        WHERE strftime('%Y', date) = ?
        GROUP BY month, category
        ORDER BY month, category
    """, [str(year)]).fetchall()
    conn.close()

    # Fill all 12 months, zeros for missing
    result = []
    for m in range(1, 13):
        mm = f"{m:02d}"
        income_e = 0.0
        expense_e = 0.0
        for row in rows:
            if row[0] == mm:
                if row[1] == "income":
                    income_e = row[2]
                else:
                    expense_e = row[2]
        result.append({"month": mm, "income": income_e, "expense": expense_e})
    return result


def add_transaction(
    tx_id: str, date: str, category: str, type_: str,
    amount: float, description: str = "", reference: str = ""
) -> dict:
    conn = _get_conn()
    now  = datetime.utcnow().isoformat()
    try:
        conn.execute("""
            INSERT INTO finance_transactions
                (tx_id, date, category, type_, amount, description, reference, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [tx_id, date, category, type_, amount, description, reference, now])
        conn.commit()
        row = conn.execute(
            "SELECT id, tx_id, date, category, type_, amount, description, reference, created_at "
            "FROM finance_transactions WHERE tx_id=?", [tx_id]
        ).fetchone()
        conn.close()
        return {"id": row[0], "tx_id": row[1], "date": row[2], "category": row[3],
                "type": row[4], "amount": row[5], "description": row[6],
                "reference": row[7], "created_at": row[8]}
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"Transaction with tx_id {tx_id!r} already exists") from e


# ─── Student Tuition functions ────────────────────────────────────────────────

def tuition_now():
    return datetime.utcnow().isoformat()


def get_all_students(status=None) -> list[dict]:
    conn = _get_conn()
    if status:
        rows = conn.execute(
            "SELECT student_id, name, grade, school, monthly_amount, status, created_at, updated_at "
            "FROM student_tuition WHERE status=? ORDER BY student_id",
            [status]
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT student_id, name, grade, school, monthly_amount, status, created_at, updated_at "
            "FROM student_tuition ORDER BY student_id"
        ).fetchall()
    conn.close()
    return [_row_to_student(r) for r in rows]


def _row_to_student(r):
    return {
        "student_id": r[0], "name": r[1], "grade": r[2], "school": r[3],
        "monthly_amount": r[4], "status": r[5], "created_at": r[6], "updated_at": r[7],
    }


def get_student(student_id: str) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT student_id, name, grade, school, monthly_amount, status, created_at, updated_at "
        "FROM student_tuition WHERE student_id=?",
        [student_id]
    ).fetchone()
    conn.close()
    return _row_to_student(row) if row else None


def add_student(student_id: str, name: str, grade: int, school: str,
                monthly_amount: int, status: str = "active") -> dict:
    conn = _get_conn()
    now = tuition_now()
    try:
        conn.execute("""
            INSERT INTO student_tuition (student_id, name, grade, school, monthly_amount, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [student_id, name, grade, school, monthly_amount, status, now, now])
        conn.commit()
        conn.close()
        return get_student(student_id)
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"Student with ID {student_id!r} already exists") from e


def update_student(student_id: str, **fields) -> dict | None:
    allowed = ["name", "grade", "school", "monthly_amount", "status"]
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_student(student_id)
    updates["updated_at"] = tuition_now()
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn = _get_conn()
    conn.execute(f"UPDATE student_tuition SET {set_clause} WHERE student_id=?",
                 list(updates.values()) + [student_id])
    conn.commit()
    conn.close()
    return get_student(student_id)


def delete_student(student_id: str) -> bool:
    conn = _get_conn()
    cur = conn.execute("DELETE FROM student_tuition WHERE student_id=?", [student_id])
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def get_payments(student_id: str = None, month: str = None) -> list[dict]:
    conn = _get_conn()
    query = "SELECT id, student_id, month, payment_date, amount_paid, notes, created_at FROM tuition_payments WHERE 1=1"
    params = []
    if student_id:
        query += " AND student_id=?"
        params.append(student_id)
    if month:
        query += " AND month=?"
        params.append(month)
    query += " ORDER BY student_id, month"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_payment(r) for r in rows]


def _row_to_payment(r):
    return {
        "id": r[0], "student_id": r[1], "month": r[2],
        "payment_date": r[3], "amount_paid": r[4], "notes": r[5], "created_at": r[6],
    }


def add_payment(student_id: str, month: str, payment_date: str = None,
                amount_paid: int = 0, notes: str = "") -> dict:
    now = tuition_now()
    conn = _get_conn()
    conn.execute("""
        INSERT INTO tuition_payments (student_id, month, payment_date, amount_paid, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [student_id, month, payment_date, amount_paid, notes, now])
    conn.commit()
    row = conn.execute(
        "SELECT id, student_id, month, payment_date, amount_paid, notes, created_at "
        "WHERE student_id=? AND month=?", [student_id, month]
    ).fetchone()
    conn.close()
    # Re-fetch properly
    rows = conn.execute(
        "SELECT id, student_id, month, payment_date, amount_paid, notes, created_at "
        "FROM tuition_payments WHERE student_id=? AND month=? ORDER BY id DESC LIMIT 1",
        [student_id, month]
    ).fetchall()
    return _row_to_payment(rows[0]) if rows else None


def update_payment(payment_id: int, **fields) -> dict | None:
    allowed = ["student_id", "month", "payment_date", "amount_paid", "notes"]
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        conn = _get_conn()
        row = conn.execute("SELECT id, student_id, month, payment_date, amount_paid, notes, created_at FROM tuition_payments WHERE id=?", [payment_id]).fetchone()
        conn.close()
        return _row_to_payment(row) if row else None
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn = _get_conn()
    conn.execute(f"UPDATE tuition_payments SET {set_clause} WHERE id=?", list(updates.values()) + [payment_id])
    conn.commit()
    row = conn.execute("SELECT id, student_id, month, payment_date, amount_paid, notes, created_at FROM tuition_payments WHERE id=?", [payment_id]).fetchone()
    conn.close()
    return _row_to_payment(row) if row else None


def get_tuition_summary(month: str = None) -> dict:
    """Summary: total students, total monthly expected, total collected, outstanding."""
    conn = _get_conn()
    total_students = conn.execute("SELECT COUNT(*) FROM student_tuition WHERE status='active'").fetchone()[0]
    total_monthly  = conn.execute("SELECT COALESCE(SUM(monthly_amount),0) FROM student_tuition WHERE status='active'").fetchone()[0]

    if month:
        paid_row = conn.execute(
            "SELECT COALESCE(SUM(amount_paid),0) FROM tuition_payments WHERE month=?", [month]
        ).fetchone()
        total_paid = paid_row[0] if paid_row else 0
    else:
        total_paid = conn.execute("SELECT COALESCE(SUM(amount_paid),0) FROM tuition_payments").fetchone()[0]

    return {
        "total_students": total_students,
        "total_monthly_expected": total_monthly,
        "total_collected": total_paid,
        "outstanding": total_monthly - total_paid,
    }


def get_student_payment_status() -> list[dict]:
    """All students with their payment record per month (last 12 months)."""
    conn = _get_conn()
    students = get_all_students(status="active")
    MONTHS = ["January 2026","February 2026","March 2026","April 2026","May 2026","June 2026",
              "July 2026","August 2026","September 2026","October 2026","November 2026","December 2026"]
    result = []
    for s in students:
        row = {"student_id": s["student_id"], "name": s["name"], "grade": s["grade"],
               "school": s["school"], "monthly_amount": s["monthly_amount"], "status": s["status"]}
        payment_rows = {
            r[0]: r[1]
            for r in conn.execute(
                "SELECT month, amount_paid FROM tuition_payments WHERE student_id=?",
                [s["student_id"]]
            ).fetchall()
        }
        row["payments"] = {m: payment_rows.get(m, 0) for m in MONTHS}
        result.append(row)
    conn.close()
    return result


def get_monthly_breakdown(month: str) -> dict:
    """Monthly breakdown for a specific month: expected vs paid per student."""
    conn = _get_conn()
    students = get_all_students(status="active")
    rows_paid = {
        r[0]: (r[1], r[2])
        for r in conn.execute(
            "SELECT student_id, amount_paid, payment_date FROM tuition_payments WHERE month=?",
            [month]
        ).fetchall()
    }
    total_expected = sum(s["monthly_amount"] for s in students)
    total_paid = sum(v[0] for v in rows_paid.values()) if rows_paid else 0
    conn.close()

    detail = []
    for s in students:
        paid_info = rows_paid.get(s["student_id"], (0, None))
        detail.append({
            "student_id": s["student_id"], "name": s["name"],
            "grade": s["grade"], "school": s["school"],
            "monthly_amount": s["monthly_amount"],
            "amount_paid": paid_info[0] if isinstance(paid_info, tuple) else paid_info,
            "payment_date": paid_info[1] if isinstance(paid_info, tuple) else None,
            "outstanding": s["monthly_amount"] - (paid_info[0] if isinstance(paid_info, tuple) else paid_info),
        })
    return {"month": month, "total_expected": total_expected, "total_paid": total_paid,
            "total_outstanding": total_expected - total_paid, "students": detail}
