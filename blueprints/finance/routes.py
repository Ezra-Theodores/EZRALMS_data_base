"""
Finance blueprint routes — all protected by require_finance_auth.
"""
import io, csv
from flask import Blueprint, request, jsonify, render_template, Response

from ..auth_decorators import require_finance_auth
from .models import (
    get_all_transactions,
    get_summary,
    get_monthly_breakdown,
    add_transaction,
)

finance_bp = Blueprint("finance", __name__, url_prefix="/finance",
                       template_folder="templates",
                       static_folder="static")


# ─── Protected endpoints ────────────────────────────────────────────────────

@finance_bp.route("/dashboard", methods=["GET"])
@require_finance_auth
def dashboard():
    """Main HTML dashboard."""
    return render_template("finance_dashboard.html")


@finance_bp.route("/summary", methods=["GET"])
@require_finance_auth
def summary():
    """
    JSON summary for embedding.
    Query params: start_date, end_date (YYYY-MM-DD)
    """
    start = request.args.get("start_date")
    end   = request.args.get("end_date")
    data  = get_summary(start, end)
    data["monthly"] = get_monthly_breakdown(datetime.utcnow().year)
    return jsonify(data)


@finance_bp.route("/report", methods=["GET"])
@require_finance_auth
def report():
    """
    Full P&L table with optional filters.
    Query params: start_date, end_date, category (income|expense)
    """
    start  = request.args.get("start_date")
    end    = request.args.get("end_date")
    cat    = request.args.get("category")
    rows   = get_all_transactions(start, end, cat)
    return jsonify({"transactions": rows})


@finance_bp.route("/report/csv", methods=["GET"])
@require_finance_auth
def report_csv():
    """Download current filtered report as CSV."""
    start = request.args.get("start_date")
    end   = request.args.get("end_date")
    cat   = request.args.get("category")
    rows  = get_all_transactions(start, end, cat)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Date", "Category", "Type", "Amount (IDR)", "Description", "Reference", "Created At"])
    for r in rows:
        writer.writerow([r["date"], r["category"], r["type"], r["amount"],
                        r["description"], r["reference"], r["created_at"]])

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=finance_report.csv",
            "Cache-Control": "no-store",
        },
    )


# ─── Data-entry endpoints (authenticated + validated) ───────────────────────

@finance_bp.route("/transaction", methods=["POST"])
@require_finance_auth
def create_transaction():
    """Add a new income or expense transaction."""
    body = request.get_json(silent=True) or {}
    required = ["tx_id", "date", "category", "type", "amount"]
    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400

    if body["category"] not in ("income", "expense"):
        return jsonify({"error": "category must be 'income' or 'expense'"}), 400

    try:
        tx = add_transaction(
            tx_id=str(body["tx_id"]),
            date=str(body["date"]),
            category=str(body["category"]),
            type_=str(body["type"]),
            amount=float(body["amount"]),
            description=str(body.get("description", "")),
            reference=str(body.get("reference", "")),
        )
        return jsonify({"success": True, "transaction": tx}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({"error": "Failed to create transaction", "detail": str(e)}), 500


# ─── Health check (no auth — used by monitoring) ─────────────────────────────

@finance_bp.route("/health", methods=["GET"])
def health():
    """No auth required."""
    return jsonify({"status": "ok"})


from datetime import datetime
