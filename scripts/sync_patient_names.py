"""Nightly sync: HosXP patient (hn, pname, fname, lname) -> local patient_names cache.

Run inside the web container via cron (not part of the Flask app process):
    docker compose exec -T web python scripts/sync_patient_names.py
instance/app.db is owned by root inside the container (created by gunicorn
running as root) — a bare host `uv run` can't write to it, hence `exec`
rather than running this from the host venv. Replaces the table contents in
one transaction so the gunicorn workers reading/writing instance/app.db
never see a dropped table.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.models.local_db import get_db_session
from app.models.patient_name import PatientName
from app.services.hosxp_service import execute_sql_on_hosxp


def sync():
    df = execute_sql_on_hosxp("patient_search.sql")
    rows = df.to_dict("records")

    with get_db_session() as db:
        db.query(PatientName).delete()
        db.bulk_insert_mappings(PatientName, rows)

    print(f"synced {len(rows)} patient names")


if __name__ == "__main__":
    sync()
