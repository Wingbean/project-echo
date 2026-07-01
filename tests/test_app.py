# tests/test_app.py - Basic Application Tests
import os
import sys

# Ensure config can build a SECRET_KEY before `app` is imported (fail-fast in prod).
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
