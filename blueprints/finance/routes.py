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
    get_all_students, get_student, add_student, update_student, delete_student,
    get_payments, add_payment, update_payment,
    get_tuition_summary, get_student_payment_status, get_monthly_breakdown as get_tuition_monthly,
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


# ─── Student Tuition API ──────────────────────────────────────────────────────

@finance_bp.route("/students", methods=["GET"])
@require_finance_auth
def list_students():
    status = request.args.get("status")
    return jsonify({"students": get_all_students(status=status)})


@finance_bp.route("/students", methods=["POST"])
@require_finance_auth
def create_student():
    body = request.get_json(silent=True) or {}
    for field in ["student_id", "name", "grade", "school", "monthly_amount"]:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400
    try:
        student = add_student(
            student_id=str(body["student_id"]),
            name=str(body["name"]),
            grade=int(body["grade"]),
            school=str(body["school"]),
            monthly_amount=int(body["monthly_amount"]),
            status=str(body.get("status", "active")),
        )
        return jsonify({"success": True, "student": student}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({"error": "Failed to create student", "detail": str(e)}), 500


@finance_bp.route("/students/<student_id>", methods=["PUT"])
@require_finance_auth
def edit_student(student_id):
    body = request.get_json(silent=True) or {}
    student = update_student(student_id, **body)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"success": True, "student": student})


@finance_bp.route("/students/<student_id>", methods=["DELETE"])
@require_finance_auth
def remove_student(student_id):
    if delete_student(student_id):
        return jsonify({"success": True})
    return jsonify({"error": "Student not found"}), 404


@finance_bp.route("/students/<student_id>/payments", methods=["GET"])
@require_finance_auth
def list_payments(student_id):
    if not get_student(student_id):
        return jsonify({"error": "Student not found"}), 404
    month = request.args.get("month")
    return jsonify({"payments": get_payments(student_id=student_id, month=month)})


@finance_bp.route("/students/<student_id>/payments", methods=["POST"])
@require_finance_auth
def create_payment(student_id):
    if not get_student(student_id):
        return jsonify({"error": "Student not found"}), 404
    body = request.get_json(silent=True) or {}
    if "month" not in body:
        return jsonify({"error": "Missing field: month"}), 400
    try:
        payment = add_payment(
            student_id=student_id,
            month=str(body["month"]),
            payment_date=str(body.get("payment_date", "")),
            amount_paid=int(body.get("amount_paid", 0)),
            notes=str(body.get("notes", "")),
        )
        return jsonify({"success": True, "payment": payment}), 201
    except Exception as e:
        return jsonify({"error": "Failed to record payment", "detail": str(e)}), 500


@finance_bp.route("/payments/<int:payment_id>", methods=["PUT"])
@require_finance_auth
def edit_payment(payment_id):
    body = request.get_json(silent=True) or {}
    payment = update_payment(payment_id, **body)
    if not payment:
        return jsonify({"error": "Payment record not found"}), 404
    return jsonify({"success": True, "payment": payment})


# ─── Tuition Reports ─────────────────────────────────────────────────────────

@finance_bp.route("/reports/summary", methods=["GET"])
@require_finance_auth
def tuition_summary():
    month = request.args.get("month")
    data = get_tuition_summary(month=month)
    return jsonify(data)


@finance_bp.route("/reports/students", methods=["GET"])
@require_finance_auth
def tuition_students_report():
    return jsonify({"students": get_student_payment_status()})


@finance_bp.route("/reports/monthly", methods=["GET"])
@require_finance_auth
def tuition_monthly_report():
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "month query param required, e.g. January 2026"}), 400
    return jsonify(get_tuition_monthly(month))


from datetime import datetime
