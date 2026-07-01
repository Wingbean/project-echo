# app/api/routes.py - API Endpoints (JSON responses)
import os
import json
import time
import re
import hmac

from flask import jsonify, request, session
from sqlalchemy import text

from app.api import api_bp
from app import csrf
from app.config import Config
from app.models.connection import get_hosxp_connection
from app.services.hosxp_service import execute_sql_on_hosxp
from app.utils.helpers import records_from_df


# --- Secret Code Verification ---

def _verify_secret_code(session_key: str):
    """Shared verification logic for secret-code protected pages.

    Args:
        session_key: Session key to set on success (e.g. 'echo_authenticated').

    Returns:
        Flask JSON response tuple.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("code"):
        return jsonify({"status": "error", "message": "กรุณาระบุรหัส"}), 400

    code = str(data["code"]).strip()
    correct_code = Config.ECHO_SECRET_CODE

    if not correct_code:
        return jsonify({"status": "error", "message": "ECHO_SECRET_CODE not configured"}), 500

    # constant-time comparison to avoid leaking the code via timing
    if not hmac.compare_digest(code, correct_code):
        return jsonify({"status": "error", "message": "รหัสไม่ถูกต้อง"}), 401

    session[session_key] = True
    return jsonify({"status": "success", "message": "ยืนยันรหัสสำเร็จ"})


@api_bp.route("/verify_echo", methods=["POST"])
def verify_echo():
    """Verify secret code for Echo page access."""
    return _verify_secret_code("echo_authenticated")


@api_bp.route("/verify_emr", methods=["POST"])
def verify_emr():
    """Verify secret code for EMR page access."""
    return _verify_secret_code("emr_authenticated")


# --- Per-HN search endpoints ---

def _hn_search(sql_file: str, zfill: bool = True):
    """Shared per-HN lookup: validate HN, run the SQL, serialize the result.

    Args:
        sql_file: SQL filename in sql/ (e.g. 'egfr.sql').
        zfill: Zero-pad HN to 7 digits (True for most; consult/flow_opd pass
               False on purpose — see CLAUDE.md).
    """
    data = request.get_json(silent=True)
    if not data or not data.get("hn"):
        return jsonify({"status": "error", "message": "กรุณาระบุ HN"}), 400

    hn = str(data["hn"]).strip()
    if zfill:
        hn = hn.zfill(7)

    if not re.match(r"^\d+$", hn):
        return jsonify({"status": "error", "message": "HN ต้องเป็นตัวเลขเท่านั้น"}), 400

    try:
        columns, records = records_from_df(
            execute_sql_on_hosxp(sql_file, params={"hn": hn})
        )
        return jsonify({
            "status": "success",
            "columns": columns,
            "records": records,
            "total": len(records),
        })
    except Exception as e:
        print(f"❌ {sql_file} query failed: {e}")
        return jsonify({"status": "error", "message": "เกิดข้อผิดพลาดในการดึงข้อมูล"}), 500


@api_bp.route("/egfr", methods=["POST"])
def egfr_search():
    """Search eGFR records by HN."""
    return _hn_search("egfr.sql")


@api_bp.route("/a1c", methods=["POST"])
def a1c_search():
    """Search A1C records by HN."""
    return _hn_search("a1c.sql")


@api_bp.route("/inr", methods=["POST"])
def inr_search():
    """Search INR records by HN."""
    return _hn_search("inr.sql")


@api_bp.route("/consult", methods=["POST"])
def consult_search():
    """Search doctor consult records by HN (HN not zero-padded)."""
    return _hn_search("consult.sql", zfill=False)


@api_bp.route("/flow_opd", methods=["POST"])
def flow_opd_search():
    """Search today's OPD flow records by HN (HN not zero-padded)."""
    return _hn_search("flow_opd.sql", zfill=False)


@api_bp.route("/emr", methods=["POST"])
def emr_search():
    """Search EMR records by HN. Requires EMR authentication.

    Fetches Hx/PE/Dx/OP plus prescriptions, grouping rx rows by VN onto
    each record as `rx_list`.
    """
    # PHI: the /emr page gates access; the API must too. Both /emr and the
    # integrated /echo dashboard (echo_authenticated) legitimately read EMR,
    # and both are gated by the same secret code — so accept either.
    if not (session.get("emr_authenticated") or session.get("echo_authenticated")):
        return jsonify({"status": "error", "message": "กรุณายืนยันรหัสก่อนเข้าใช้งาน"}), 401

    data = request.get_json(silent=True)
    if not data or not data.get("hn"):
        return jsonify({"status": "error", "message": "กรุณาระบุ HN"}), 400

    hn = str(data["hn"]).strip().zfill(7)
    if not re.match(r"^\d+$", hn):
        return jsonify({"status": "error", "message": "HN ต้องเป็นตัวเลขเท่านั้น"}), 400

    try:
        columns, records = records_from_df(
            execute_sql_on_hosxp("emr_hx_pe_dx_op.sql", params={"hn": hn})
        )

        # Rx is best-effort — missing rx shouldn't fail the whole record fetch.
        try:
            _, rx_records = records_from_df(
                execute_sql_on_hosxp("emr_rx.sql", params={"hn": hn})
            )
        except Exception as e:
            print(f"❌ emr_rx query failed: {e}")
            rx_records = []

        rx_by_vn = {}
        for rx in rx_records:
            vn = str(rx.get("vn", ""))
            if vn:
                rx_by_vn.setdefault(vn, []).append(rx)

        for record in records:
            record["rx_list"] = rx_by_vn.get(str(record.get("VN", "")), [])

        return jsonify({
            "status": "success",
            "columns": columns,
            "records": records,
            "total": len(records),
        })
    except Exception as e:
        print(f"❌ emr query failed: {e}")
        return jsonify({"status": "error", "message": "เกิดข้อผิดพลาดในการดึงข้อมูล"}), 500


# --- Database Test ---

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


# --- Barcode Trigger Endpoint ---

_BARCODE_CACHE_FILE = os.path.join(Config.INSTANCE_DIR, "barcode_cache.json")


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
