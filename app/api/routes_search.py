# app/api/routes_search.py - Per-HN search endpoints (labs, EMR)
import re

from flask import jsonify, request

from app.api import api_bp
from app.services.hosxp_service import execute_sql_on_hosxp
from app.utils.auth import get_current_user, login_required
from app.utils.helpers import records_from_df


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
@login_required
def egfr_search(current_user):
    """Search eGFR records by HN."""
    return _hn_search("egfr.sql")


@api_bp.route("/a1c", methods=["POST"])
@login_required
def a1c_search(current_user):
    """Search A1C records by HN."""
    return _hn_search("a1c.sql")


@api_bp.route("/inr", methods=["POST"])
@login_required
def inr_search(current_user):
    """Search INR records by HN."""
    return _hn_search("inr.sql")


@api_bp.route("/consult", methods=["POST"])
@login_required
def consult_search(current_user):
    """Search doctor consult records by HN (HN not zero-padded)."""
    return _hn_search("consult.sql", zfill=False)


@api_bp.route("/flow_opd", methods=["POST"])
@login_required
def flow_opd_search(current_user):
    """Search today's OPD flow records by HN (HN not zero-padded)."""
    return _hn_search("flow_opd.sql", zfill=False)


@api_bp.route("/emr", methods=["POST"])
def emr_search():
    """Search EMR records by HN. Requires EMR authentication.

    Fetches Hx/PE/Dx/OP plus prescriptions, grouping rx rows by VN onto
    each record as `rx_list`.
    """
    # PHI: the /emr page gates access; the API must too. Both /emr and the
    # integrated /echo dashboard legitimately read EMR, so either access flag
    # is accepted (not access_required, which only checks a single flag).
    user = get_current_user()
    if user is None or not (user.is_verified and user.is_active):
        return jsonify({"status": "error", "message": "กรุณาเข้าสู่ระบบก่อนเข้าใช้งาน"}), 401
    if not (user.can_access_emr or user.can_access_echo):
        return jsonify({"status": "error", "message": "ไม่มีสิทธิ์เข้าถึง"}), 403

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
