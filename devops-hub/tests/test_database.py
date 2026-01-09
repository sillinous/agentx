"""
Tests for the database layer.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from core.database import (
    Database,
    DatabaseConfig,
    AgentRepository,
    WorkflowRepository,
    ExecutionRepository,
    EventRepository,
)


@pytest.fixture
def temp_db():
    """Create a temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    config = DatabaseConfig(path=db_path)
    db = Database(config)
    yield db
    db.close()
    db_path.unlink(missing_ok=True)


class TestDatabase:
    """Tests for Database class."""

    def test_database_creation(self, temp_db):
        assert temp_db is not None
        assert temp_db.config.path.exists()

    def test_execute_query(self, temp_db):
        with temp_db.cursor() as cur:
            cur.execute("SELECT 1 as value")
            row = cur.fetchone()
            assert row["value"] == 1

    def test_tables_created(self, temp_db):
        tables = temp_db.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        table_names = {t["name"] for t in tables}
        assert "agents" in table_names
        assert "workflows" in table_names
        assert "workflow_executions" in table_names
        assert "events" in table_names
        assert "api_keys" in table_names


class TestAgentRepository:
    """Tests for AgentRepository."""

    @pytest.fixture
    def repo(self, temp_db):
        return AgentRepository(temp_db)

    def test_save_and_get(self, repo):
        agent = {
            "id": "test-agent",
            "name": "Test Agent",
            "version": "1.0.0",
            "status": "production",
            "domain": "utility",
            "type": "worker",
            "description": "A test agent",
            "capabilities": ["cap1", "cap2"],
            "protocols": ["a2a/1.0"],
        }
        repo.save(agent)

        retrieved = repo.get("test-agent")
        assert retrieved is not None
        assert retrieved["id"] == "test-agent"
        assert retrieved["name"] == "Test Agent"
        assert "cap1" in retrieved["capabilities"]

    def test_get_nonexistent(self, repo):
        assert repo.get("nonexistent") is None

    def test_list_all(self, repo):
        repo.save({"id": "agent-1", "name": "Agent 1"})
        repo.save({"id": "agent-2", "name": "Agent 2"})

        all_agents = repo.list_all()
        assert len(all_agents) == 2

    def test_find_by_domain(self, repo):
        repo.save({"id": "a1", "name": "A1", "domain": "system"})
        repo.save({"id": "a2", "name": "A2", "domain": "utility"})
        repo.save({"id": "a3", "name": "A3", "domain": "system"})

        system_agents = repo.find(domain="system")
        assert len(system_agents) == 2

    def test_find_by_capability(self, repo):
        repo.save({"id": "a1", "name": "A1", "capabilities": ["analysis"]})
        repo.save({"id": "a2", "name": "A2", "capabilities": ["reporting"]})

        result = repo.find(capability="analysis")
        assert len(result) == 1
        assert result[0]["id"] == "a1"

    def test_update_agent(self, repo):
        repo.save({"id": "agent", "name": "Original"})
        repo.save({"id": "agent", "name": "Updated"})

        agent = repo.get("agent")
        assert agent["name"] == "Updated"
        assert repo.count() == 1

    def test_delete(self, repo):
        repo.save({"id": "agent", "name": "Agent"})
        assert repo.count() == 1

        result = repo.delete("agent")
        assert result is True
        assert repo.count() == 0

    def test_count(self, repo):
        assert repo.count() == 0
        repo.save({"id": "a1", "name": "A1"})
        repo.save({"id": "a2", "name": "A2"})
        assert repo.count() == 2


class TestWorkflowRepository:
    """Tests for WorkflowRepository."""

    @pytest.fixture
    def repo(self, temp_db):
        return WorkflowRepository(temp_db)

    def test_save_and_get(self, repo):
        workflow = {
            "id": "wf-1",
            "name": "Test Workflow",
            "description": "A test workflow",
            "version": "1.0.0",
            "steps": [
                {"name": "Step 1", "type": "agent"},
                {"name": "Step 2", "type": "agent"},
            ],
        }
        repo.save(workflow)

        retrieved = repo.get("wf-1")
        assert retrieved is not None
        assert retrieved["name"] == "Test Workflow"
        assert len(retrieved["steps"]) == 2

    def test_list_all(self, repo):
        repo.save({"id": "wf-1", "name": "Workflow 1"})
        repo.save({"id": "wf-2", "name": "Workflow 2"})

        all_workflows = repo.list_all()
        assert len(all_workflows) == 2

    def test_delete(self, repo):
        repo.save({"id": "wf-1", "name": "Workflow 1"})
        assert repo.delete("wf-1") is True
        assert repo.get("wf-1") is None


class TestExecutionRepository:
    """Tests for ExecutionRepository."""

    @pytest.fixture
    def repo(self, temp_db):
        return ExecutionRepository(temp_db)

    def test_save_and_get(self, repo):
        execution = {
            "id": "exec-1",
            "workflow_id": "wf-1",
            "workflow_name": "Test Workflow",
            "status": "completed",
            "current_step": 2,
            "context": {"input": {"x": 1}},
            "results": {"step1": "done"},
            "errors": [],
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }
        repo.save(execution)

        retrieved = repo.get("exec-1")
        assert retrieved is not None
        assert retrieved["status"] == "completed"
        assert retrieved["context"]["input"]["x"] == 1

    def test_find_by_workflow(self, repo):
        repo.save({"id": "e1", "workflow_id": "wf-1", "workflow_name": "WF1"})
        repo.save({"id": "e2", "workflow_id": "wf-2", "workflow_name": "WF2"})
        repo.save({"id": "e3", "workflow_id": "wf-1", "workflow_name": "WF1"})

        wf1_execs = repo.find(workflow_id="wf-1")
        assert len(wf1_execs) == 2

    def test_find_by_status(self, repo):
        repo.save({"id": "e1", "workflow_id": "wf", "workflow_name": "WF", "status": "completed"})
        repo.save({"id": "e2", "workflow_id": "wf", "workflow_name": "WF", "status": "failed"})
        repo.save({"id": "e3", "workflow_id": "wf", "workflow_name": "WF", "status": "completed"})

        completed = repo.find(status="completed")
        assert len(completed) == 2


class TestEventRepository:
    """Tests for EventRepository."""

    @pytest.fixture
    def repo(self, temp_db):
        return EventRepository(temp_db, max_events=100)

    def test_save_and_find(self, repo):
        event = {
            "id": "evt-1",
            "type": "test.event",
            "source": "test",
            "data": {"message": "hello"},
            "timestamp": datetime.utcnow().isoformat(),
        }
        repo.save(event)

        events = repo.find(event_type="test.event")
        assert len(events) == 1
        assert events[0]["data"]["message"] == "hello"

    def test_find_by_source(self, repo):
        now = datetime.utcnow().isoformat()
        repo.save({"id": "e1", "type": "t", "source": "src1", "timestamp": now})
        repo.save({"id": "e2", "type": "t", "source": "src2", "timestamp": now})

        src1_events = repo.find(source="src1")
        assert len(src1_events) == 1

    def test_find_limit(self, repo):
        now = datetime.utcnow().isoformat()
        for i in range(10):
            repo.save({"id": f"e{i}", "type": "t", "source": "s", "timestamp": now})

        events = repo.find(limit=5)
        assert len(events) == 5
