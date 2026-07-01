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
from app.models.local_db import get_db_session
from app.models.user import User
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


def _make_active_user(email, can_access_echo=False, can_access_emr=False):
    """Insert a verified+active, 2FA-enrolled user in the test (in-memory) DB, return its id."""
    with get_db_session() as db:
        user = User(
            email=email,
            google_sub=f"sub-{email}",
            is_verified=True,
            is_active=True,
            can_access_echo=can_access_echo,
            can_access_emr=can_access_emr,
            totp_enabled=True,
            totp_secret="JBSWY3DPEHPK3PXP",
        )
        db.add(user)
        db.flush()
        return user.id


def _login_session(client, user_id):
    """Set the session as if the user finished Google login + TOTP verification."""
    with client.session_transaction() as s:
        s["user_id"] = user_id
        s["totp_verified"] = True


class TestRoutes:
    def test_index_page_requires_login(self, client):
        assert client.get("/").status_code == 302

    def test_index_page_logged_in(self, client):
        user_id = _make_active_user("home-user@example.com")
        _login_session(client, user_id)
        assert client.get("/").status_code == 200

    def test_egfr_page_requires_login(self, client):
        assert client.get("/egfr").status_code == 302

    def test_egfr_api_requires_auth(self, client):
        resp = client.post("/api/egfr", json={"hn": "123"})
        assert resp.status_code == 401

    def test_emr_api_requires_auth(self, client):
        """PHI endpoint must reject unauthenticated callers (not just the page)."""
        resp = client.post("/api/emr", json={"hn": "123"})
        assert resp.status_code == 401

    def test_hn_search_rejects_non_digit(self, client):
        user_id = _make_active_user("hn-user@example.com")
        _login_session(client, user_id)
        resp = client.post("/api/egfr", json={"hn": "abc"})
        assert resp.status_code == 400


# execute_sql_on_hosxp is looked up in routes_search, so patch it there.
_EXEC = "app.api.routes_search.execute_sql_on_hosxp"


class TestPerHNEndpoints:
    def _login(self, client, email):
        user_id = _make_active_user(email)
        _login_session(client, user_id)

    def test_egfr_success_and_zfill(self, client):
        self._login(client, "egfr-success-user@example.com")
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
        self._login(client, "consult-user@example.com")
        df = pd.DataFrame([{"x": 1}])
        with patch(_EXEC, return_value=df) as m:
            resp = client.post("/api/consult", json={"hn": "123"})
        assert resp.status_code == 200
        # consult/flow_opd intentionally keep the raw HN (CLAUDE.md)
        m.assert_called_once_with("consult.sql", params={"hn": "123"})

    def test_db_error_returns_generic_message(self, client):
        self._login(client, "db-error-user@example.com")
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
        user_id = _make_active_user("echo-user@example.com", can_access_echo=True)
        _login_session(client, user_id)
        with patch(_EXEC, side_effect=lambda f, params=None: dfs[f]):
            resp = client.post("/api/emr", json={"hn": "123"})
        assert resp.status_code == 200
        records = resp.get_json()["records"]
        by_vn = {r["VN"]: r["rx_list"] for r in records}
        assert len(by_vn["V1"]) == 2
        assert len(by_vn["V2"]) == 1

    def test_emr_allows_emr_session(self, client):
        user_id = _make_active_user("emr-user@example.com", can_access_emr=True)
        _login_session(client, user_id)
        with patch(_EXEC, return_value=pd.DataFrame([{"VN": "V1"}])):
            resp = client.post("/api/emr", json={"hn": "123"})
        assert resp.status_code == 200


class TestTwoFactorAuth:
    def _make_pending_user(self, email, totp_enabled=False, totp_secret=None):
        with get_db_session() as db:
            user = User(
                email=email,
                google_sub=f"sub-{email}",
                is_verified=True,
                is_active=True,
                totp_enabled=totp_enabled,
                totp_secret=totp_secret,
            )
            db.add(user)
            db.flush()
            return user.id

    def test_login_required_redirects_to_setup_when_not_enrolled(self, client):
        user_id = self._make_pending_user("no2fa-user@example.com")
        with client.session_transaction() as s:
            s["user_id"] = user_id
        resp = client.get("/")
        assert resp.status_code == 302
        assert "/auth/setup-2fa" in resp.headers["Location"]

    def test_login_required_redirects_to_verify_when_enrolled(self, client):
        import pyotp

        secret = pyotp.random_base32()
        user_id = self._make_pending_user("2fa-user@example.com", totp_enabled=True, totp_secret=secret)
        with client.session_transaction() as s:
            s["user_id"] = user_id
        resp = client.get("/")
        assert resp.status_code == 302
        assert "/auth/verify-2fa" in resp.headers["Location"]

    def test_setup_2fa_enrolls_with_correct_code(self, client):
        import pyotp

        user_id = self._make_pending_user("enroll-user@example.com")
        with client.session_transaction() as s:
            s["user_id"] = user_id

        client.get("/auth/setup-2fa")  # generates and stores the secret
        with get_db_session() as db:
            secret = db.get(User, user_id).totp_secret
        assert secret

        code = pyotp.TOTP(secret).now()
        resp = client.post("/auth/setup-2fa", data={"code": code})
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/")

        with get_db_session() as db:
            assert db.get(User, user_id).totp_enabled is True

    def test_verify_2fa_rejects_wrong_code(self, client):
        import pyotp

        secret = pyotp.random_base32()
        user_id = self._make_pending_user("wrongcode-user@example.com", totp_enabled=True, totp_secret=secret)
        with client.session_transaction() as s:
            s["user_id"] = user_id

        resp = client.post("/auth/verify-2fa", data={"code": "000000"})
        assert resp.status_code == 200  # re-rendered with an error, not redirected
        with client.session_transaction() as s:
            assert not s.get("totp_verified")

    def test_verify_2fa_accepts_correct_code(self, client):
        import pyotp

        secret = pyotp.random_base32()
        user_id = self._make_pending_user("rightcode-user@example.com", totp_enabled=True, totp_secret=secret)
        with client.session_transaction() as s:
            s["user_id"] = user_id

        code = pyotp.TOTP(secret).now()
        resp = client.post("/auth/verify-2fa", data={"code": code})
        assert resp.status_code == 302
        with client.session_transaction() as s:
            assert s.get("totp_verified") is True


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
