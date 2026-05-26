"""
/api/automation/*  -  Ported from app_complete.py

Start/stop the EzraLms persistent browser and the autopilot G8 Node.js script.
Subprocess handles are kept module-level — single user / single instance.
"""

import os
import subprocess
from flask import Blueprint, jsonify, current_app

bp = Blueprint("automation", __name__, url_prefix="/api/automation")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTOMATION_DIR = os.path.join(ROOT, "EzraLms_automation")

_browser_proc: "subprocess.Popen | None" = None
_autopilot_proc: "subprocess.Popen | None" = None


def _alive(p):
    return p is not None and p.poll() is None


@bp.route("/ping")
def ping():
    return jsonify({"success": True, "blueprint": "automation"})


@bp.route("/status", methods=["GET"])
def status():
    return jsonify({
        "success": True,
        "browser_running": _alive(_browser_proc),
        "autopilot_running": _alive(_autopilot_proc),
    })


@bp.route("/start", methods=["POST"])
def start_browser():
    global _browser_proc
    try:
        if _alive(_browser_proc):
            return jsonify({"success": False, "error": "Browser is already running"})

        script = os.path.join(AUTOMATION_DIR, "persistent_browser.js")
        _browser_proc = subprocess.Popen(
            ["node", script], cwd=AUTOMATION_DIR,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return jsonify({"success": True, "message": "Browser started"})
    except Exception as e:
        current_app.logger.error(f"Browser start failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@bp.route("/stop", methods=["POST"])
def stop_all():
    global _browser_proc, _autopilot_proc
    try:
        if _alive(_browser_proc):
            _browser_proc.terminate()
        _browser_proc = None

        if _alive(_autopilot_proc):
            _autopilot_proc.terminate()
        _autopilot_proc = None

        return jsonify({"success": True, "message": "Automation stopped"})
    except Exception as e:
        current_app.logger.error(f"Stop failed: {e}")
        return jsonify({"success": False, "error": str(e)})


@bp.route("/autopilot", methods=["POST"])
def autopilot():
    global _autopilot_proc
    try:
        if not _alive(_browser_proc):
            return jsonify({"success": False, "error": "Start the persistent browser first"})
        if _alive(_autopilot_proc):
            return jsonify({"success": False, "error": "Autopilot is already running"})

        script = os.path.join(AUTOMATION_DIR, "autopilot_g8.js")
        _autopilot_proc = subprocess.Popen(
            ["node", script], cwd=AUTOMATION_DIR,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        return jsonify({"success": True, "message": "Autopilot G8 started"})
    except Exception as e:
        current_app.logger.error(f"Autopilot start failed: {e}")
        return jsonify({"success": False, "error": str(e)})
