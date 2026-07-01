# tests/test_app.py - Basic Application Tests
import os
import sys

# Ensure config can build a SECRET_KEY before `app` is imported (fail-fast in prod).
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch

import pandas as pd
import pytest

from app import create_app
from app.utils.helpers import records_from_df


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


class TestRoutes:
    def test_index_page(self, client):
        assert client.get("/").status_code == 200

    def test_egfr_page(self, client):
        assert client.get("/egfr").status_code == 200

    def test_emr_api_requires_auth(self, client):
        """PHI endpoint must reject unauthenticated callers (not just the page)."""
        resp = client.post("/api/emr", json={"hn": "123"})
        assert resp.status_code == 401

    def test_hn_search_rejects_non_digit(self, client):
        resp = client.post("/api/egfr", json={"hn": "abc"})
        assert resp.status_code == 400


# execute_sql_on_hosxp is looked up in routes_search, so patch it there.
_EXEC = "app.api.routes_search.execute_sql_on_hosxp"


class TestPerHNEndpoints:
    def test_egfr_success_and_zfill(self, client):
        df = pd.DataFrame([{"HN": "0000123", "result": 42}])
        with patch(_EXEC, return_value=df) as m:
            resp = client.post("/api/egfr", json={"hn": "123"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "success"
        assert body["total"] == 1
        assert body["columns"] == ["HN", "result"]
        # HN zero-padded to 7 before the query
        m.assert_called_once_with("egfr.sql", params={"hn": "0000123"})

    def test_consult_does_not_zfill(self, client):
        df = pd.DataFrame([{"x": 1}])
        with patch(_EXEC, return_value=df) as m:
            resp = client.post("/api/consult", json={"hn": "123"})
        assert resp.status_code == 200
        # consult/flow_opd intentionally keep the raw HN (CLAUDE.md)
        m.assert_called_once_with("consult.sql", params={"hn": "123"})

    def test_db_error_returns_generic_message(self, client):
        with patch(_EXEC, side_effect=RuntimeError("secret: table hosxp.foo")):
            resp = client.post("/api/egfr", json={"hn": "123"})
        assert resp.status_code == 500
        # internal detail must not leak to the client
        assert "hosxp" not in resp.get_json()["message"].lower()

    def test_emr_groups_rx_by_vn(self, client):
        main = pd.DataFrame([{"VN": "V1", "dx": "A"}, {"VN": "V2", "dx": "B"}])
        rx = pd.DataFrame([
            {"vn": "V1", "drug": "para"},
            {"vn": "V1", "drug": "amox"},
            {"vn": "V2", "drug": "asa"},
        ])
        dfs = {"emr_hx_pe_dx_op.sql": main, "emr_rx.sql": rx}
        with client.session_transaction() as s:
            s["echo_authenticated"] = True
        with patch(_EXEC, side_effect=lambda f, params=None: dfs[f]):
            resp = client.post("/api/emr", json={"hn": "123"})
        assert resp.status_code == 200
        records = resp.get_json()["records"]
        by_vn = {r["VN"]: r["rx_list"] for r in records}
        assert len(by_vn["V1"]) == 2
        assert len(by_vn["V2"]) == 1

    def test_emr_allows_emr_session(self, client):
        with client.session_transaction() as s:
            s["emr_authenticated"] = True
        with patch(_EXEC, return_value=pd.DataFrame([{"VN": "V1"}])):
            resp = client.post("/api/emr", json={"hn": "123"})
        assert resp.status_code == 200


class TestSerializer:
    def test_records_from_df_serializes_types(self):
        df = pd.DataFrame([{
            "ts": pd.Timestamp("2024-01-15 10:30:00"),
            "td": pd.Timedelta("0 days 22:00:10"),
            "num": 5,
            "s": "hello",
        }])
        cols, recs = records_from_df(df)
        assert cols == ["ts", "td", "num", "s"]
        r = recs[0]
        assert r["ts"] == "2024-01-15T10:30:00"
        assert r["td"] == "22:00:10"
        assert r["num"] == 5
        assert r["s"] == "hello"

    def test_nat_and_null_become_empty(self):
        df = pd.DataFrame({"d": [pd.Timestamp("2024-01-01"), pd.NaT], "x": [None, "v"]})
        _, recs = records_from_df(df)
        assert recs[0]["d"] == "2024-01-01T00:00:00"
        assert recs[1]["d"] == ""
        assert recs[0]["x"] == ""
