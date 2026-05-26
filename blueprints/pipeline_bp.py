"""
/api/pipeline/*  -  Thin proxy facade for the DATA_HOUSE_EZRALMS Raw->JSON pipeline.

The full pipeline (PDF/OCR + Gemini/BytePlus + MySQL writes) lives in
DATA_HOUSE_EZRALMS/server_v2.py and depends on heavy modules (pdfplumber,
google-genai, byteplus-sdk, sqlalchemy). Phase 1 does NOT pull those into
the unified process. Instead this blueprint:

  * exposes /api/pipeline/ping and /api/pipeline/status so the unified UI can
    discover whether the pipeline backend is reachable, and
  * lets the operator point a PIPELINE_BACKEND env var at the running
    server_v2 instance (e.g. http://localhost:5000) and proxies upload calls.

Phase 2 will move the pipeline logic into this blueprint directly.
"""

import os
import requests
from flask import Blueprint, jsonify, request, Response

bp = Blueprint("pipeline", __name__, url_prefix="/api/pipeline")

PIPELINE_BACKEND = os.getenv("PIPELINE_BACKEND", "").rstrip("/")


@bp.route("/ping")
def ping():
    return jsonify({"success": True, "blueprint": "pipeline", "backend": PIPELINE_BACKEND or None})


@bp.route("/status")
def status():
    """Probe the upstream server_v2 if configured."""
    if not PIPELINE_BACKEND:
        return jsonify({
            "success": False,
            "configured": False,
            "hint": "Set PIPELINE_BACKEND=http://host:port (URL of DATA_HOUSE_EZRALMS/server_v2.py)",
        })
    try:
        r = requests.get(f"{PIPELINE_BACKEND}/", timeout=3)
        return jsonify({"success": True, "configured": True, "upstream_status": r.status_code})
    except Exception as e:
        return jsonify({"success": False, "configured": True, "error": str(e)})


@bp.route("/proxy/<path:upstream_path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(upstream_path):
    """Generic proxy: /api/pipeline/proxy/upload -> PIPELINE_BACKEND/upload"""
    if not PIPELINE_BACKEND:
        return jsonify({"success": False, "error": "PIPELINE_BACKEND not configured"}), 503

    url = f"{PIPELINE_BACKEND}/{upstream_path}"
    try:
        upstream = requests.request(
            method=request.method,
            url=url,
            params=request.args,
            data=request.get_data(),
            headers={k: v for k, v in request.headers if k.lower() != "host"},
            cookies=request.cookies,
            allow_redirects=False,
            timeout=120,
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"upstream error: {e}"}), 502

    excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    headers = [(k, v) for k, v in upstream.raw.headers.items() if k.lower() not in excluded]
    return Response(upstream.content, upstream.status_code, headers)
