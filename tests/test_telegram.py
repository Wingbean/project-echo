# tests/test_telegram.py - Sync notification formatting & no-op safety
import os
import sys

os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch

from app.utils.telegram import get_system_status, send_telegram
from scripts.sync_patient_names import _report


def test_get_system_status_format():
    status = get_system_status()
    assert status.startswith("Disk: ")
    assert "% used | RAM: " in status
    assert status.endswith("% used")


def test_send_telegram_noop_without_config():
    with patch("app.utils.telegram.Config.TELEGRAM_BOT_TOKEN", ""):
        with patch("requests.post") as mock_post:
            send_telegram("hello")
            mock_post.assert_not_called()


def test_report_success():
    msg = _report(success=True)
    assert "✅" in msg
    assert "Project Echo Sync" in msg
    assert "📦 ตาราง: patient_names" in msg
    assert "❗" not in msg


def test_report_failure_includes_error():
    msg = _report(success=False, error="connection refused")
    assert "🚨" in msg
    assert "Project Echo Sync Failed" in msg
    assert "📦 ตาราง: patient_names" in msg
    assert "❗ connection refused" in msg
