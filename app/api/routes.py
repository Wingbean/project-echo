# app/api/routes.py - API Endpoints (JSON responses)
import os
import json
import threading
import time
import re

from flask import jsonify, request
from app.api import api_bp
from app import csrf
from app.config import Config
from app.models.connection import get_hosxp_connection
from app.services.hosxp_service import (
    sync_data_from_hosxp,
    get_last_sync_time,
    execute_sql_on_hosxp,
)
from app.services.render_service import get_dashboard_data, get_table_data
from app.utils.validators import validate_date, validate_table_name
from app.utils.helpers import get_current_month_range

# Sync status file path
_SYNC_STATUS_FILE = os.path.join(Config.INSTANCE_DIR, "sync_status.json")


def _set_sync_status(status_dict: dict):
    """Write sync status to file (atomic)."""
    try:
        os.makedirs(Config.INSTANCE_DIR, exist_ok=True)
        tmp_file = _SYNC_STATUS_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(status_dict, f, ensure_ascii=False)
        os.replace(tmp_file, _SYNC_STATUS_FILE)
    except Exception as e:
        print(f"Error writing sync status: {e}")


def _get_sync_status() -> dict:
    """Read current sync status."""
    if not os.path.exists(_SYNC_STATUS_FILE):
        return {"status": "idle", "message": "ไม่มีการซิงค์ข้อมูล"}

    for _ in range(3):
        try:
            with open(_SYNC_STATUS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except Exception:
            pass
        time.sleep(0.5)

    return {"status": "running", "message": "กำลังตรวจสอบสถานะการซิงค์..."}


def _verify_sync_pin() -> tuple[bool, dict]:
    """Verify the sync PIN from request headers.

    Returns:
        Tuple of (is_valid, error_response).
    """
    pin = request.headers.get("X-Sync-Pin")
    correct_pin = Config.SYNC_PIN

    if not correct_pin:
        return False, {"status": "error", "message": "SYNC_PIN not configured"}
    if pin != correct_pin:
        return False, {"status": "error", "message": "รหัสผ่านไม่ถูกต้อง (Invalid PIN)"}
    return True, {}


# --- Sync Endpoints ---

@api_bp.route("/sync", methods=["GET"])
@csrf.exempt
def sync_data():
    """Trigger a full data sync from HosXP to SQLite.

    Requires X-Sync-Pin header for authentication.
    Runs in background thread to prevent timeout.
    """
    is_valid, error = _verify_sync_pin()
    if not is_valid:
        return jsonify(error), 401

    current_status = _get_sync_status()
    if current_status.get("status") == "running":
        return jsonify({
            "status": "running",
            "message": "การซิงค์ข้อมูลกำลังทำงานอยู่ กรุณารอสักครู่",
        })

    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    if not start_date or not end_date:
        start_date, end_date = get_current_month_range()

    if not validate_date(start_date) or not validate_date(end_date):
        return jsonify({"status": "error", "message": "รูปแบบวันที่ไม่ถูกต้อง"}), 400

    _set_sync_status({"status": "running", "message": "กำลังซิงค์ข้อมูล..."})

    def _run():
        try:
            result = sync_data_from_hosxp(start_date, end_date)
            _set_sync_status(result)
            print(f"✅ Background sync completed: {result.get('status')}")
        except Exception as e:
            _set_sync_status({"status": "error", "message": str(e)})
            print(f"❌ Background sync failed: {e}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({"status": "started", "message": "เริ่มซิงค์ข้อมูลแล้ว กรุณารอสักครู่..."})


@api_bp.route("/sync-auto", methods=["GET"])
@csrf.exempt
def sync_auto():
    """Trigger an automatic sync (excludes historical data)."""
    is_valid, error = _verify_sync_pin()
    if not is_valid:
        return jsonify(error), 401

    current_status = _get_sync_status()
    if current_status.get("status") == "running":
        return jsonify({
            "status": "running",
            "message": "การซิงค์ข้อมูลกำลังทำงานอยู่ กรุณารอสักครู่",
        })

    _set_sync_status({"status": "running", "message": "กำลังซิงค์ข้อมูลอัตโนมัติ..."})

    def _run():
        try:
            start_date, end_date = get_current_month_range()
            result = sync_data_from_hosxp(start_date, end_date)
            _set_sync_status(result)
        except Exception as e:
            _set_sync_status({"status": "error", "message": str(e)})

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return jsonify({"status": "started", "message": "เริ่มซิงค์ข้อมูลอัตโนมัติแล้ว"})


@api_bp.route("/sync-status", methods=["GET"])
@csrf.exempt
def sync_status():
    """Check the current sync status."""
    return jsonify(_get_sync_status())


@api_bp.route("/last-sync", methods=["GET"])
@csrf.exempt
def last_sync():
    """Get the last sync timestamp."""
    return jsonify({"last_sync": get_last_sync_time()})


# --- Data Endpoints ---

@api_bp.route("/dashboard-data", methods=["GET"])
@csrf.exempt
def dashboard_data():
    """Get all dashboard data from SQLite cache."""
    data = get_dashboard_data()
    return jsonify(data)


@api_bp.route("/table/<table_name>", methods=["GET"])
@csrf.exempt
def table_data(table_name: str):
    """Get data for a specific cached table.

    Args:
        table_name: Name of the SQLite table (URL path parameter).
    """
    if not validate_table_name(table_name):
        return jsonify({"status": "error", "message": "ชื่อตารางไม่ถูกต้อง"}), 400

    data = get_table_data(table_name)
    return jsonify(data)


@api_bp.route("/query", methods=["POST"])
def execute_query():
    """Execute a query on cached SQLite data.

    Expects JSON body with:
        - table_name: Name of table to query.
        - filters: Optional dict of column:value filters.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"status": "error", "message": "กรุณาส่งข้อมูล JSON"}), 400

    table_name = data.get("table_name", "")
    if not validate_table_name(table_name):
        return jsonify({"status": "error", "message": "ชื่อตารางไม่ถูกต้อง"}), 400

    result = get_table_data(table_name)
    return jsonify(result)


# --- eGFR Endpoint ---

@api_bp.route("/egfr", methods=["POST"])
def egfr_search():
    """Search eGFR records by HN.

    Expects JSON body with:
        - hn: Patient hospital number (string).

    Returns:
        JSON with columns and records from egfr.sql.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("hn"):
        return jsonify({"status": "error", "message": "กรุณาระบุ HN"}), 400

    hn = str(data["hn"]).strip()
    hn = hn.zfill(7) # pad with leading zeros, just to be safe at backend

    # Validate HN: only digits allowed
    if not re.match(r"^\d+$", hn):
        return jsonify({"status": "error", "message": "HN ต้องเป็นตัวเลขเท่านั้น"}), 400

    try:
        df = execute_sql_on_hosxp("egfr.sql", params={"hn": hn})
        # Replace NaN/NaT with empty strings to ensure valid JSON
        df = df.fillna("")
        columns = df.columns.tolist()
        records = df.to_dict(orient="records")

        # Convert date/datetime/timedelta objects to strings for JSON serialization
        for record in records:
            for key, val in record.items():
                if hasattr(val, "components"): # For pandas Timedelta
                    ts = str(val).split()[-1]
                    record[key] = ts.split('.')[0]
                elif hasattr(val, "isoformat"):
                    dt_str = val.isoformat()
                    record[key] = "" if dt_str == "NaT" else dt_str
                elif val is None:
                    record[key] = ""
                else:
                    record[key] = str(val) if not isinstance(val, (int, float, str, bool)) else val

        return jsonify({
            "status": "success",
            "columns": columns,
            "records": records,
            "total": len(records),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- A1C Endpoint ---

@api_bp.route("/a1c", methods=["POST"])
def a1c_search():
    """Search A1C records by HN.

    Expects JSON body with:
        - hn: Patient hospital number (string).

    Returns:
        JSON with columns and records from a1c.sql.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("hn"):
        return jsonify({"status": "error", "message": "กรุณาระบุ HN"}), 400

    hn = str(data["hn"]).strip()
    hn = hn.zfill(7) # pad with leading zeros

    # Validate HN: only digits allowed
    if not re.match(r"^\d+$", hn):
        return jsonify({"status": "error", "message": "HN ต้องเป็นตัวเลขเท่านั้น"}), 400

    try:
        df = execute_sql_on_hosxp("a1c.sql", params={"hn": hn})
        df = df.fillna("")
        columns = df.columns.tolist()
        records = df.to_dict(orient="records")

        # Convert objects to strings for JSON
        for record in records:
            for key, val in record.items():
                if hasattr(val, "components"):
                    ts = str(val).split()[-1]
                    record[key] = ts.split('.')[0]
                elif hasattr(val, "isoformat"):
                    dt_str = val.isoformat()
                    record[key] = "" if dt_str == "NaT" else dt_str
                elif val is None:
                    record[key] = ""
                else:
                    record[key] = str(val) if not isinstance(val, (int, float, str, bool)) else val

        return jsonify({
            "status": "success",
            "columns": columns,
            "records": records,
            "total": len(records),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- EMR Endpoint ---

@api_bp.route("/emr", methods=["POST"])
def emr_search():
    """Search EMR records by HN.

    Expects JSON body with:
        - hn: Patient hospital number (string).

    Returns:
        JSON with columns and records from emr_hx_pe_dx_op.sql.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("hn"):
        return jsonify({"status": "error", "message": "กรุณาระบุ HN"}), 400

    hn = str(data["hn"]).strip()
    hn = hn.zfill(7) # pad with leading zeros

    # Validate HN: only digits allowed
    if not re.match(r"^\d+$", hn):
        return jsonify({"status": "error", "message": "HN ต้องเป็นตัวเลขเท่านั้น"}), 400

    try:
        # Fetch Diagnosis and History
        df = execute_sql_on_hosxp("emr_hx_pe_dx_op.sql", params={"hn": hn})
        df = df.fillna("")
        columns = df.columns.tolist()
        records = df.to_dict(orient="records")

        # Fetch Rx data
        try:
            rx_df = execute_sql_on_hosxp("emr_rx.sql", params={"hn": hn})
            rx_df = rx_df.fillna("")
            rx_records = rx_df.to_dict(orient="records")
        except Exception as e:
            print(f"Failed to fetch rx data: {e}")
            rx_records = []

        # Group Rx records by VN
        rx_by_vn = {}
        for rx in rx_records:
            vn = str(rx.get("vn", ""))
            if not vn: continue
            if vn not in rx_by_vn:
                rx_by_vn[vn] = []
            
            # Formatting values for Rx serialization
            processed_rx = {}
            for key, val in rx.items():
                if hasattr(val, "components"):
                    ts = str(val).split()[-1]
                    processed_rx[key] = ts.split('.')[0]
                elif hasattr(val, "isoformat"):
                    dt_str = val.isoformat()
                    processed_rx[key] = "" if dt_str == "NaT" else dt_str
                elif val is None:
                    processed_rx[key] = ""
                else:
                    processed_rx[key] = str(val) if not isinstance(val, (int, float, str, bool)) else val
                    
            rx_by_vn[vn].append(processed_rx)

        # Merge Rx into records
        for record in records:
            vn = str(record.get("VN", ""))
            record["rx_list"] = rx_by_vn.get(vn, [])
            
            # Convert objects to strings for JSON
            for key, val in record.items():
                if key == "rx_list": continue
                if hasattr(val, "components"):
                    ts = str(val).split()[-1]
                    record[key] = ts.split('.')[0]
                elif hasattr(val, "isoformat"):
                    dt_str = val.isoformat()
                    record[key] = "" if dt_str == "NaT" else dt_str
                elif val is None:
                    record[key] = ""
                else:
                    record[key] = str(val) if not isinstance(val, (int, float, str, bool)) else val

        return jsonify({
            "status": "success",
            "columns": columns,
            "records": records,
            "total": len(records),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Consult Endpoint ---

@api_bp.route("/consult", methods=["POST"])
def consult_search():
    """Search doctor consult records by HN.

    Expects JSON body with:
        - hn: Patient hospital number (string).

    Returns:
        JSON with columns and records from doctor_consult table.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("hn"):
        return jsonify({"status": "error", "message": "กรุณาระบุ HN"}), 400

    hn = str(data["hn"]).strip()

    # Validate HN: only digits allowed
    if not re.match(r"^\d+$", hn):
        return jsonify({"status": "error", "message": "HN ต้องเป็นตัวเลขเท่านั้น"}), 400

    try:
        df = execute_sql_on_hosxp("consult.sql", params={"hn": hn})
        # Replace NaN/NaT with empty strings to ensure valid JSON
        df = df.fillna("")
        columns = df.columns.tolist()
        records = df.to_dict(orient="records")

        # Convert date/datetime objects to strings for JSON serialization
        for record in records:
            for key, val in record.items():
                if hasattr(val, "components"): # For pandas Timedelta
                    ts = str(val).split()[-1]
                    record[key] = ts.split('.')[0]
                elif hasattr(val, "isoformat"):
                    dt_str = val.isoformat()
                    record[key] = "" if dt_str == "NaT" else dt_str
                elif val is None:
                    record[key] = ""

        return jsonify({
            "status": "success",
            "columns": columns,
            "records": records,
            "total": len(records),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- OPD Flow Endpoint ---

@api_bp.route("/flow_opd", methods=["POST"])
def flow_opd_search():
    """Search OPD Flow records by HN for today.

    Expects JSON body with:
        - hn: Patient hospital number (string).

    Returns:
        JSON with columns and records from flow_opd.sql.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("hn"):
        return jsonify({"status": "error", "message": "กรุณาระบุ HN"}), 400

    hn = str(data["hn"]).strip()

    # Validate HN: only digits allowed
    if not re.match(r"^\d+$", hn):
        return jsonify({"status": "error", "message": "HN ต้องเป็นตัวเลขเท่านั้น"}), 400

    try:
        df = execute_sql_on_hosxp("flow_opd.sql", params={"hn": hn})
        # Replace NaN/NaT with empty strings to ensure valid JSON
        df = df.fillna("")
        columns = df.columns.tolist()
        records = df.to_dict(orient="records")

        # Convert date/datetime/timedelta objects to strings for JSON serialization
        for record in records:
            for key, val in record.items():
                if hasattr(val, "components"): # For pandas Timedelta
                    # str(val) is like "0 days 22:00:10", we extract just time
                    ts = str(val).split()[-1]
                    record[key] = ts.split('.')[0]
                elif hasattr(val, "isoformat"):
                    dt_str = val.isoformat()
                    record[key] = "" if dt_str == "NaT" else dt_str
                elif val is None:
                    record[key] = ""
                else:
                    record[key] = str(val) if not isinstance(val, (int, float, str, bool)) else val

        return jsonify({
            "status": "success",
            "columns": columns,
            "records": records,
            "total": len(records),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Database Test ---

@api_bp.route("/test-db", methods=["GET"])
@csrf.exempt
def test_db():
    """Test HosXP database connection."""
    try:
        with get_hosxp_connection() as conn:
            result = conn.execute(__import__("sqlalchemy").text("SELECT VERSION()"))
            version = result.fetchone()[0]
        return jsonify({
            "status": "success",
            "message": "Connected to HosXP successfully!",
            "db_version": version,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
