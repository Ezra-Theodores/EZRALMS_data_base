"""
Auth decorators for protected blueprints.
"""
import os
import base64
from functools import wraps
from flask import request, jsonify


def _get_finance_username():
    return os.environ.get("FINANCE_USERNAME", "Imel")


def _get_finance_password():
    pwd = os.environ.get("FINANCE_PASSWORD")
    if not pwd:
        raise RuntimeError(
            "FINANCE_PASSWORD environment variable is not set. "
            "Set it before starting the app (e.g. FINANCE_PASSWORD=yourpassword)."
        )
    return pwd


def require_finance_auth(f):
    """
    HTTP Basic Auth decorator for the finance blueprint.
    Checks Authorization: Basic <base64(username:password)> header.
    The username must match FINANCE_USERNAME and the password must match
    FINANCE_PASSWORD (both checked). Returns 401 + WWW-Authenticate
    header if either is wrong or missing.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Basic "):
            return (
                jsonify({"error": "Unauthorized", "message": "Basic auth required"}),
                401,
                {"WWW-Authenticate": 'Basic realm="EZRALMS Finance"'},
            )

        try:
            encoded = auth_header[6:]  # strip "Basic "
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            return (
                jsonify({"error": "Unauthorized", "message": "Invalid auth format"}),
                401,
                {"WWW-Authenticate": 'Basic realm="EZRALMS Finance"'},
            )

        if username != _get_finance_username() or password != _get_finance_password():
            return (
                jsonify({"error": "Unauthorized", "message": "Incorrect username or password"}),
                401,
                {"WWW-Authenticate": 'Basic realm="EZRALMS Finance"'},
            )

        return f(*args, **kwargs)

    return decorated
