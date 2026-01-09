"""
Tests for the workflow engine.
"""

import pytest

from service.workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStatus,
    StepType,
    get_workflow_engine,
)


class TestWorkflowStep:
    """Tests for WorkflowStep."""

    def test_step_creation(self):
        step = WorkflowStep(
            name="Test Step",
            type=StepType.AGENT,
            agent_id="test-agent",
            capability="test-cap",
        )
        assert step.name == "Test Step"
        assert step.type == StepType.AGENT
        assert step.agent_id == "test-agent"

    def test_step_with_input_mapping(self):
        step = WorkflowStep(
            name="Step with mapping",
            type=StepType.AGENT,
            agent_id="test-agent",
            capability="test-cap",
            input_mapping={"param1": "input.value1", "param2": "context.result"},
            output_key="step_result",
        )
        assert step.input_mapping["param1"] == "input.value1"
        assert step.output_key == "step_result"

    def test_parallel_step(self):
        step = WorkflowStep(
            name="Parallel Step",
            type=StepType.PARALLEL,
            parallel_steps=[
                WorkflowStep(name="Sub1", type=StepType.AGENT, agent_id="a1", capability="c1"),
                WorkflowStep(name="Sub2", type=StepType.AGENT, agent_id="a2", capability="c2"),
            ],
        )
        assert len(step.parallel_steps) == 2


class TestWorkflowDefinition:
    """Tests for WorkflowDefinition."""

    def test_definition_creation(self):
        workflow = WorkflowDefinition(
            name="Test Workflow",
            description="A test workflow",
            version="1.0.0",
            steps=[
                WorkflowStep(name="Step 1", type=StepType.AGENT, agent_id="a1", capability="c1"),
                WorkflowStep(name="Step 2", type=StepType.AGENT, agent_id="a2", capability="c2"),
            ],
        )
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 2

    def test_definition_has_id(self):
        workflow = WorkflowDefinition(name="Test")
        assert workflow.id is not None
        assert len(workflow.id) > 0


class TestWorkflowExecution:
    """Tests for WorkflowExecution."""

    def test_execution_creation(self):
        execution = WorkflowExecution(
            workflow_id="wf-123",
            workflow_name="Test Workflow",
        )
        assert execution.status == WorkflowStatus.PENDING
        assert execution.current_step == 0
        assert execution.context == {}

    def test_execution_to_dict(self):
        execution = WorkflowExecution(
            workflow_id="wf-123",
            workflow_name="Test Workflow",
            status=WorkflowStatus.RUNNING,
        )
        d = execution.to_dict()
        assert d["workflow_id"] == "wf-123"
        assert d["status"] == "running"


class TestWorkflowEngine:
    """Tests for WorkflowEngine."""

    @pytest.fixture
    def engine(self):
        return WorkflowEngine()

    def test_builtin_workflows_registered(self, engine):
        workflows = engine.list_workflows()
        assert len(workflows) >= 5

        workflow_ids = [w["id"] for w in workflows]
        assert "research-report" in workflow_ids
        assert "comprehensive-code-review" in workflow_ids
        assert "project-planning" in workflow_ids

    def test_get_workflow(self, engine):
        workflow = engine.get_workflow("research-report")
        assert workflow is not None
        assert workflow.name == "Research & Report Generation"
        assert len(workflow.steps) >= 1

    def test_get_workflow_not_found(self, engine):
        workflow = engine.get_workflow("nonexistent")
        assert workflow is None

    def test_register_workflow(self, engine):
        custom_workflow = WorkflowDefinition(
            name="Custom Workflow",
            description="A custom test workflow",
            steps=[
                WorkflowStep(
                    name="Custom Step",
                    type=StepType.AGENT,
                    agent_id="research-analyzer",
                    capability="market-analysis",
                ),
            ],
        )

        workflow_id = engine.register_workflow(custom_workflow)
        assert workflow_id == custom_workflow.id

        retrieved = engine.get_workflow(workflow_id)
        assert retrieved is not None
        assert retrieved.name == "Custom Workflow"

    def test_list_workflows(self, engine):
        workflows = engine.list_workflows()
        assert isinstance(workflows, list)

        for w in workflows:
            assert "id" in w
            assert "name" in w
            assert "description" in w
            assert "steps_count" in w

    @pytest.mark.asyncio
    async def test_execute_workflow(self, engine):
        execution = await engine.execute_workflow(
            "research-report",
            {"market": "AI", "region": "global"},
        )

        assert execution is not None
        assert execution.workflow_id == "research-report"
        assert execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]
        assert execution.started_at is not None

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, engine):
        with pytest.raises(ValueError):
            await engine.execute_workflow("nonexistent", {})

    @pytest.mark.asyncio
    async def test_execute_workflow_stores_results(self, engine):
        execution = await engine.execute_workflow(
            "research-report",
            {"market": "Technology"},
        )

        if execution.status == WorkflowStatus.COMPLETED:
            assert len(execution.results) > 0

    def test_get_execution(self, engine):
        # Execute a workflow first
        import asyncio
        execution = asyncio.get_event_loop().run_until_complete(
            engine.execute_workflow("research-report", {})
        )

        retrieved = engine.get_execution(execution.id)
        assert retrieved is not None
        assert retrieved.id == execution.id

    def test_list_executions(self, engine):
        # Execute workflows
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            engine.execute_workflow("research-report", {})
        )

        executions = engine.list_executions()
        assert len(executions) >= 1

    def test_list_executions_filtered(self, engine):
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            engine.execute_workflow("research-report", {})
        )

        executions = engine.list_executions(workflow_id="research-report")
        for e in executions:
            assert e["workflow_id"] == "research-report"

    @pytest.mark.asyncio
    async def test_workflow_context_passing(self, engine):
        """Test that data passes between steps via context."""
        execution = await engine.execute_workflow(
            "research-report",
            {"market": "TestMarket"},
        )

        # Input should be in context
        assert "input" in execution.context
        assert execution.context["input"]["market"] == "TestMarket"

    def test_resolve_path(self, engine):
        context = {
            "input": {"market": "AI", "region": "US"},
            "step1_result": {"data": "value"},
        }

        result = engine._resolve_path(context, "input.market")
        assert result == "AI"

        result = engine._resolve_path(context, "step1_result.data")
        assert result == "value"

        result = engine._resolve_path(context, "nonexistent.path")
        assert result is None


class TestWorkflowEngineGlobal:
    """Tests for global workflow engine instance."""

    def test_get_workflow_engine_singleton(self):
        engine1 = get_workflow_engine()
        engine2 = get_workflow_engine()
        assert engine1 is engine2

    def test_get_workflow_engine_has_builtin_workflows(self):
        engine = get_workflow_engine()
        workflows = engine.list_workflows()
        assert len(workflows) >= 5
