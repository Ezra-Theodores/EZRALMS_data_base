"""
Finance blueprint registration.
Verifies FINANCE_USERNAME and FINANCE_PASSWORD are set at import time (fail-fast).
"""
import os
from .routes import finance_bp

# Fail fast — crash immediately if not set, rather than exposing a 500 later
if not os.environ.get("FINANCE_USERNAME"):
    raise RuntimeError(
        "FINANCE_USERNAME environment variable is not set. "
        "The finance blueprint cannot start without it."
    )

if not os.environ.get("FINANCE_PASSWORD"):
    raise RuntimeError(
        "FINANCE_PASSWORD environment variable is not set. "
        "The finance blueprint cannot start without it."
    )

__all__ = ["finance_bp"]
