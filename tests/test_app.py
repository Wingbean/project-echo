# tests/test_app.py - Basic Application Tests
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["FLASK_ENV"] = "testing"
    os.environ["WTF_CSRF_ENABLED"] = "false"

    application = create_app()
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    yield application


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestBasicRoutes:
    """Test that basic page routes respond correctly."""

    def test_index_page(self, client):
        """Homepage should return 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_query_page(self, client):
        """Query page should return 200."""
        response = client.get("/query")
        assert response.status_code == 200

    def test_results_page(self, client):
        """Results page should return 200."""
        response = client.get("/results")
        assert response.status_code == 200


class TestAPIRoutes:
    """Test API endpoints."""

    def test_dashboard_data(self, client):
        """Dashboard data API should return JSON."""
        response = client.get("/api/dashboard-data")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_sync_status(self, client):
        """Sync status API should return JSON."""
        response = client.get("/api/sync-status")
        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data

    def test_last_sync(self, client):
        """Last sync API should return timestamp."""
        response = client.get("/api/last-sync")
        assert response.status_code == 200
        data = response.get_json()
        assert "last_sync" in data

    def test_sync_without_pin(self, client):
        """Sync without PIN should return 401."""
        response = client.get("/api/sync")
        assert response.status_code == 401

    def test_table_invalid_name(self, client):
        """Invalid table name should return 400."""
        response = client.get("/api/table/DROP TABLE users")
        assert response.status_code == 400


class TestSecurity:
    """Test security features."""

    def test_csrf_token_in_query_page(self, app):
        """Query page should contain CSRF token."""
        app.config["WTF_CSRF_ENABLED"] = True
        with app.test_client() as client:
            response = client.get("/query")
            assert b"csrf_token" in response.data
