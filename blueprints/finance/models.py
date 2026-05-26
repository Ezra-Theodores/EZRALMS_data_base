"""
Finance data models.
Reads from finance_transactions table in ezralms_unified.db.
Creates the table if it doesn't exist (schema is auto-initialized).
"""
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "ezralms_unified.db")
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
