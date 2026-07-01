# app/api/routes_barcode.py - Barcode scanner + DB diagnostic (csrf-exempt, external)
import os
import json
import time
import re

from flask import jsonify, request
from sqlalchemy import text

from app.api import api_bp
from app import csrf
from app.config import Config
from app.models.connection import get_hosxp_connection

_BARCODE_CACHE_FILE = os.path.join(Config.INSTANCE_DIR, "barcode_cache.json")


@api_bp.route("/test-db", methods=["GET"])
@csrf.exempt
def test_db():
    """Test HosXP database connection."""
    try:
        with get_hosxp_connection() as conn:
            version = conn.execute(text("SELECT VERSION()")).fetchone()[0]
        return jsonify({
            "status": "success",
            "message": "Connected to HosXP successfully!",
            "db_version": version,
        })
    except Exception as e:
        print(f"❌ test-db failed: {e}")
        return jsonify({"status": "error", "message": "เชื่อมต่อฐานข้อมูลไม่สำเร็จ"}), 500


@api_bp.route("/barcode-trigger", methods=["POST"])
@csrf.exempt
def barcode_trigger():
    """Receive HN from the background barcode scanner program."""
    data = request.get_json(silent=True)
    if not data and request.form:
        data = request.form.to_dict()

    if not data or not data.get("hn"):
        return jsonify({"status": "error", "message": "กรุณาระบุ HN"}), 400

    hn = str(data["hn"]).strip()
    if re.match(r"^\d+$", hn):
        hn = hn.zfill(7)

    try:
        os.makedirs(Config.INSTANCE_DIR, exist_ok=True)
        cache_data = {"hn": hn, "timestamp": time.time()}
        # atomic write so /last-scanned never reads a half-written file
        tmp_file = _BARCODE_CACHE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
        os.replace(tmp_file, _BARCODE_CACHE_FILE)
        return jsonify({
            "status": "success",
            "message": f"Received HN {hn}",
            "timestamp": cache_data["timestamp"],
        })
    except Exception as e:
        print(f"❌ barcode-trigger failed: {e}")
        return jsonify({"status": "error", "message": "บันทึกข้อมูลไม่สำเร็จ"}), 500


@api_bp.route("/last-scanned", methods=["GET"])
@csrf.exempt
def get_last_scanned():
    """Get the last scanned HN."""
    if not os.path.exists(_BARCODE_CACHE_FILE):
        return jsonify({"status": "success", "hn": None, "timestamp": 0})

    try:
        with open(_BARCODE_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({
            "status": "success",
            "hn": data.get("hn"),
            "timestamp": data.get("timestamp", 0),
        })
    except Exception as e:
        print(f"❌ last-scanned failed: {e}")
        return jsonify({"status": "error", "message": "อ่านข้อมูลไม่สำเร็จ"}), 500
