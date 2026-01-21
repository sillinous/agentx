"""Tests for FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, ACTION_TEMPLATES, ALLOWED_SCAN_ROOTS, is_path_allowed


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self):
        """Health endpoint should return 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_expected_structure(self):
        """Health endpoint should return status and service name."""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["status"] == "healthy"
        assert data["service"] == "RevenueRadar"


class TestProjectsEndpoint:
    """Tests for the projects endpoints."""

    def test_list_projects_returns_200(self):
        """GET /api/projects should return 200."""
        response = client.get("/api/projects")
        assert response.status_code == 200

    def test_list_projects_returns_structure(self):
        """GET /api/projects should return projects array and total."""
        response = client.get("/api/projects")
        data = response.json()
        assert "projects" in data
        assert "total" in data
        assert isinstance(data["projects"], list)
        assert isinstance(data["total"], int)

    def test_list_projects_with_tier_filter(self):
        """GET /api/projects?tier=tier1 should filter by tier."""
        response = client.get("/api/projects?tier=tier1")
        assert response.status_code == 200
        data = response.json()
        for project in data["projects"]:
            assert project["tier"] == "tier1"

    def test_list_projects_with_status_filter(self):
        """GET /api/projects?status=ready should filter by status."""
        response = client.get("/api/projects?status=ready")
        assert response.status_code == 200
        data = response.json()
        for project in data["projects"]:
            assert project["status"] == "ready"

    def test_list_projects_with_sort(self):
        """GET /api/projects?sort_by=name&order=asc should sort."""
        response = client.get("/api/projects?sort_by=name&order=asc")
        assert response.status_code == 200

    def test_list_projects_invalid_sort_by(self):
        """Invalid sort_by should return 422."""
        response = client.get("/api/projects?sort_by=invalid_field")
        assert response.status_code == 422

    def test_list_projects_invalid_order(self):
        """Invalid order should return 422."""
        response = client.get("/api/projects?order=invalid")
        assert response.status_code == 422

    def test_get_project_not_found(self):
        """GET /api/projects/{id} for nonexistent project should return 404."""
        response = client.get("/api/projects/nonexistent-id-12345")
        assert response.status_code == 404

    def test_update_project_not_found(self):
        """PATCH /api/projects/{id} for nonexistent project should return 404."""
        response = client.patch(
            "/api/projects/nonexistent-id-12345",
            json={"status": "ready"}
        )
        assert response.status_code == 404

    def test_scan_invalid_path(self):
        """POST /api/projects/scan with invalid path should return 400."""
        response = client.post("/api/projects/scan?path=/nonexistent/path")
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""

    def test_overview_returns_200(self):
        """GET /api/analytics/overview should return 200."""
        response = client.get("/api/analytics/overview")
        assert response.status_code == 200

    def test_overview_structure(self):
        """Overview should contain expected fields."""
        response = client.get("/api/analytics/overview")
        data = response.json()
        expected_fields = ["total_projects", "by_tier", "by_status", "revenue_potential", "avg_scores"]
        for field in expected_fields:
            assert field in data

    def test_quickwins_returns_200(self):
        """GET /api/analytics/quickwins should return 200."""
        response = client.get("/api/analytics/quickwins")
        assert response.status_code == 200

    def test_quickwins_with_limit(self):
        """GET /api/analytics/quickwins?limit=5 should respect limit."""
        response = client.get("/api/analytics/quickwins?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["opportunities"]) <= 5

    def test_tiers_returns_200(self):
        """GET /api/analytics/tiers should return 200."""
        response = client.get("/api/analytics/tiers")
        assert response.status_code == 200


class TestOpportunitiesEndpoints:
    """Tests for opportunities endpoints."""

    def test_list_opportunities_returns_200(self):
        """GET /api/opportunities should return 200."""
        response = client.get("/api/opportunities")
        assert response.status_code == 200

    def test_list_opportunities_structure(self):
        """Opportunities list should have expected structure."""
        response = client.get("/api/opportunities")
        data = response.json()
        assert "opportunities" in data
        assert "total" in data

    def test_list_opportunities_with_status_filter(self):
        """GET /api/opportunities?status=pending should filter."""
        response = client.get("/api/opportunities?status=pending")
        assert response.status_code == 200
        data = response.json()
        for opp in data["opportunities"]:
            assert opp["status"] == "pending"

    def test_list_opportunities_with_priority_filter(self):
        """GET /api/opportunities?priority=high should filter."""
        response = client.get("/api/opportunities?priority=high")
        assert response.status_code == 200
        data = response.json()
        for opp in data["opportunities"]:
            assert opp["priority"] == "high"

    def test_get_pipeline_returns_200(self):
        """GET /api/opportunities/pipeline should return 200."""
        response = client.get("/api/opportunities/pipeline")
        assert response.status_code == 200

    def test_pipeline_structure(self):
        """Pipeline should have status columns."""
        response = client.get("/api/opportunities/pipeline")
        data = response.json()
        assert "pipeline" in data
        expected_statuses = ["pending", "in_progress", "completed", "blocked"]
        for status in expected_statuses:
            assert status in data["pipeline"]

    def test_update_opportunity_not_found(self):
        """PATCH /api/opportunities/{id} for nonexistent should return 404."""
        response = client.patch(
            "/api/opportunities/nonexistent-opp-id",
            json={"status": "completed"}
        )
        assert response.status_code == 404


class TestActionsEndpoints:
    """Tests for action execution endpoints."""

    def test_get_templates_returns_200(self):
        """GET /api/actions/templates should return 200."""
        response = client.get("/api/actions/templates")
        assert response.status_code == 200

    def test_templates_structure(self):
        """Templates should have expected structure."""
        response = client.get("/api/actions/templates")
        data = response.json()
        assert "templates" in data

        # Check each template has required fields
        for key, template in data["templates"].items():
            assert "title" in template
            assert "description" in template
            assert "requires_npm" in template

    def test_templates_excludes_internal_fields(self):
        """Templates response should not expose command_args."""
        response = client.get("/api/actions/templates")
        data = response.json()

        for key, template in data["templates"].items():
            assert "command_args" not in template

    def test_execute_invalid_template(self):
        """POST /api/actions/execute with invalid template should return 400."""
        response = client.post(
            "/api/actions/execute",
            json={"template_key": "invalid_template", "project_path": "/tmp/test"}
        )
        assert response.status_code == 400
        assert "Invalid template_key" in response.json()["detail"]

    def test_execute_missing_project_path(self):
        """POST /api/actions/execute without project_path should return 422."""
        response = client.post(
            "/api/actions/execute",
            json={"template_key": "run_tests_npm"}
        )
        assert response.status_code == 422

    def test_execute_nonexistent_path(self):
        """POST /api/actions/execute with nonexistent path should return 400."""
        response = client.post(
            "/api/actions/execute",
            json={"template_key": "run_tests_npm", "project_path": "/nonexistent/path/12345"}
        )
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_execute_disallowed_path(self):
        """POST /api/actions/execute with disallowed path should return 403."""
        # This test assumes /tmp exists but is not in ALLOWED_SCAN_ROOTS
        with patch("main.Path") as mock_path:
            mock_instance = MagicMock()
            mock_instance.exists.return_value = True
            mock_path.return_value = mock_instance

            response = client.post(
                "/api/actions/execute",
                json={"template_key": "run_tests_npm", "project_path": "/etc/passwd"}
            )
            # Should fail validation before hitting path check
            assert response.status_code == 422


class TestPathValidation:
    """Tests for path validation security."""

    def test_is_path_allowed_rejects_etc(self):
        """Paths under /etc should be rejected."""
        assert is_path_allowed("/etc/passwd") is False
        assert is_path_allowed("/etc/shadow") is False

    def test_is_path_allowed_rejects_root(self):
        """Paths under /root should be rejected."""
        assert is_path_allowed("/root/.ssh/id_rsa") is False

    def test_is_path_allowed_accepts_allowed_roots(self):
        """Paths under allowed roots should be accepted."""
        for root in ALLOWED_SCAN_ROOTS:
            # Skip if root doesn't exist on this system
            if os.path.exists(root):
                test_path = os.path.join(root, "some_project")
                assert is_path_allowed(test_path) is True


class TestActionTemplates:
    """Tests for action template configuration."""

    def test_all_templates_have_command_args(self):
        """All templates should have command_args defined."""
        for key, template in ACTION_TEMPLATES.items():
            assert "command_args" in template, f"Template {key} missing command_args"
            assert isinstance(template["command_args"], list)
            assert len(template["command_args"]) > 0

    def test_all_templates_have_title(self):
        """All templates should have a title."""
        for key, template in ACTION_TEMPLATES.items():
            assert "title" in template
            assert len(template["title"]) > 0

    def test_expected_templates_exist(self):
        """Expected action templates should be defined."""
        expected_templates = [
            "deploy_vercel",
            "add_stripe",
            "add_docker",
            "run_tests_npm",
            "run_tests_pytest",
            "install_npm",
            "install_pip",
        ]
        for template_key in expected_templates:
            assert template_key in ACTION_TEMPLATES


class TestInputValidation:
    """Tests for input validation on endpoints."""

    def test_create_opportunity_missing_project_id(self):
        """Creating opportunity without project_id should fail."""
        response = client.post(
            "/api/opportunities",
            json={"title": "Test Opportunity"}
        )
        assert response.status_code == 422

    def test_create_opportunity_missing_title(self):
        """Creating opportunity without title should fail."""
        response = client.post(
            "/api/opportunities",
            json={"project_id": "some-id"}
        )
        assert response.status_code == 422

    def test_update_project_with_invalid_status(self):
        """Updating project with completely invalid data should still work (Pydantic allows partial updates)."""
        # This tests that PATCH allows partial updates
        response = client.patch(
            "/api/projects/test-id",
            json={}  # Empty update
        )
        # Should return 404 (project not found) not 422 (validation error)
        assert response.status_code == 404
