"""
Workflow Engine - Orchestrates multi-agent workflows.

Enables complex multi-step processes where multiple agents collaborate
to achieve a goal. Supports sequential, parallel, and conditional execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4
from enum import Enum
import asyncio
import logging

from service.agent_loader import get_loader

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, Enum):
    AGENT = "agent"           # Execute an agent capability
    PARALLEL = "parallel"     # Execute multiple steps in parallel
    CONDITIONAL = "conditional"  # Conditional branching
    TRANSFORM = "transform"   # Transform data between steps
    WAIT = "wait"             # Wait for a condition


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    type: StepType = StepType.AGENT
    agent_id: Optional[str] = None
    capability: Optional[str] = None
    input_mapping: Dict[str, str] = field(default_factory=dict)  # Maps workflow context to step input
    output_key: Optional[str] = None  # Key to store result in context
    config: Dict[str, Any] = field(default_factory=dict)

    # For parallel steps
    parallel_steps: List["WorkflowStep"] = field(default_factory=list)

    # For conditional steps
    condition: Optional[str] = None
    if_true: Optional["WorkflowStep"] = None
    if_false: Optional["WorkflowStep"] = None


@dataclass
class WorkflowDefinition:
    """Definition of a workflow."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    steps: List[WorkflowStep] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    """A running workflow instance."""
    id: str = field(default_factory=lambda: str(uuid4()))
    workflow_id: str = ""
    workflow_name: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    current_step: int = 0
    context: Dict[str, Any] = field(default_factory=dict)  # Shared data between steps
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "current_step": self.current_step,
            "context": self.context,
            "results": self.results,
            "errors": self.errors,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class WorkflowEngine:
    """
    Executes multi-agent workflows.

    Features:
    - Sequential and parallel step execution
    - Data passing between steps via context
    - Error handling and recovery
    - Workflow state persistence
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._executions: Dict[str, WorkflowExecution] = {}
        self._loader = get_loader()

        # Register built-in workflows
        self._register_builtin_workflows()

    def _register_builtin_workflows(self):
        """Register pre-built workflow templates."""

        # Research & Report Workflow
        research_workflow = WorkflowDefinition(
            id="research-report",
            name="Research & Report Generation",
            description="Conducts market research and generates a comprehensive report",
            steps=[
                WorkflowStep(
                    name="Market Analysis",
                    type=StepType.AGENT,
                    agent_id="research-analyzer",
                    capability="market-analysis",
                    input_mapping={"market": "input.market", "region": "input.region"},
                    output_key="market_analysis",
                ),
                WorkflowStep(
                    name="Trend Prediction",
                    type=StepType.AGENT,
                    agent_id="research-analyzer",
                    capability="trend-prediction",
                    input_mapping={"topic": "input.market"},
                    output_key="trends",
                ),
                WorkflowStep(
                    name="Generate Report",
                    type=StepType.AGENT,
                    agent_id="documentation-generator",
                    capability="guide-creation",
                    input_mapping={"topic": "input.market"},
                    output_key="report",
                ),
            ],
        )
        self._workflows[research_workflow.id] = research_workflow

        # Code Review Workflow
        code_review_workflow = WorkflowDefinition(
            id="comprehensive-code-review",
            name="Comprehensive Code Review",
            description="Full code review including security, style, and performance",
            steps=[
                WorkflowStep(
                    name="Parallel Analysis",
                    type=StepType.PARALLEL,
                    parallel_steps=[
                        WorkflowStep(
                            name="Security Scan",
                            type=StepType.AGENT,
                            agent_id="code-reviewer",
                            capability="security-scanning",
                            output_key="security_results",
                        ),
                        WorkflowStep(
                            name="Style Check",
                            type=StepType.AGENT,
                            agent_id="code-reviewer",
                            capability="style-checking",
                            output_key="style_results",
                        ),
                        WorkflowStep(
                            name="Performance Analysis",
                            type=StepType.AGENT,
                            agent_id="code-reviewer",
                            capability="performance-analysis",
                            output_key="performance_results",
                        ),
                    ],
                ),
                WorkflowStep(
                    name="Generate Recommendations",
                    type=StepType.AGENT,
                    agent_id="code-reviewer",
                    capability="refactoring-suggestions",
                    output_key="recommendations",
                ),
            ],
        )
        self._workflows[code_review_workflow.id] = code_review_workflow

        # Project Planning Workflow
        project_workflow = WorkflowDefinition(
            id="project-planning",
            name="Project Planning & Decomposition",
            description="Breaks down a project into tasks with risk analysis",
            steps=[
                WorkflowStep(
                    name="Task Decomposition",
                    type=StepType.AGENT,
                    agent_id="task-decomposer",
                    capability="task-decomposition",
                    input_mapping={"task": "input.project_name"},
                    output_key="tasks",
                ),
                WorkflowStep(
                    name="Dependency Analysis",
                    type=StepType.AGENT,
                    agent_id="task-decomposer",
                    capability="dependency-analysis",
                    output_key="dependencies",
                ),
                WorkflowStep(
                    name="Risk Analysis",
                    type=StepType.AGENT,
                    agent_id="task-decomposer",
                    capability="risk-analysis",
                    output_key="risks",
                ),
                WorkflowStep(
                    name="Create Execution Plan",
                    type=StepType.AGENT,
                    agent_id="task-decomposer",
                    capability="execution-planning",
                    output_key="execution_plan",
                ),
            ],
        )
        self._workflows[project_workflow.id] = project_workflow

        # Financial Analysis Workflow
        finance_workflow = WorkflowDefinition(
            id="financial-analysis",
            name="Complete Financial Analysis",
            description="Comprehensive financial analysis with forecasting",
            steps=[
                WorkflowStep(
                    name="Financial Analysis",
                    type=StepType.AGENT,
                    agent_id="finance-analyst",
                    capability="financial-analysis",
                    input_mapping={"period": "input.period"},
                    output_key="analysis",
                ),
                WorkflowStep(
                    name="Risk Assessment",
                    type=StepType.AGENT,
                    agent_id="finance-analyst",
                    capability="risk-assessment",
                    output_key="risk_assessment",
                ),
                WorkflowStep(
                    name="Forecast",
                    type=StepType.AGENT,
                    agent_id="finance-analyst",
                    capability="forecasting",
                    input_mapping={"horizon": "input.forecast_horizon"},
                    output_key="forecast",
                ),
                WorkflowStep(
                    name="Generate Report",
                    type=StepType.AGENT,
                    agent_id="finance-analyst",
                    capability="report-generation",
                    output_key="report",
                ),
            ],
        )
        self._workflows[finance_workflow.id] = finance_workflow

        # Content Creation Pipeline
        content_workflow = WorkflowDefinition(
            id="content-pipeline",
            name="Content Creation Pipeline",
            description="End-to-end content creation with SEO optimization",
            steps=[
                WorkflowStep(
                    name="Research Topic",
                    type=StepType.AGENT,
                    agent_id="research-analyzer",
                    capability="data-aggregation",
                    input_mapping={"query": "input.topic"},
                    output_key="research",
                ),
                WorkflowStep(
                    name="Generate Content",
                    type=StepType.AGENT,
                    agent_id="content-creator",
                    capability="content-generation",
                    input_mapping={"topic": "input.topic", "tone": "input.tone"},
                    output_key="content",
                ),
                WorkflowStep(
                    name="Edit Content",
                    type=StepType.AGENT,
                    agent_id="content-creator",
                    capability="editing",
                    output_key="edited_content",
                ),
                WorkflowStep(
                    name="SEO Optimization",
                    type=StepType.AGENT,
                    agent_id="content-creator",
                    capability="seo-optimization",
                    input_mapping={"keywords": "input.keywords"},
                    output_key="seo_results",
                ),
            ],
        )
        self._workflows[content_workflow.id] = content_workflow

    def register_workflow(self, workflow: WorkflowDefinition) -> str:
        """Register a new workflow definition."""
        self._workflows[workflow.id] = workflow
        return workflow.id

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID."""
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows."""
        return [
            {
                "id": w.id,
                "name": w.name,
                "description": w.description,
                "version": w.version,
                "steps_count": len(w.steps),
            }
            for w in self._workflows.values()
        ]

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
    ) -> WorkflowExecution:
        """Execute a workflow with the given input."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Create execution instance
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            status=WorkflowStatus.RUNNING,
            context={"input": input_data},
            started_at=datetime.utcnow(),
        )
        self._executions[execution.id] = execution

        try:
            # Execute each step
            for i, step in enumerate(workflow.steps):
                execution.current_step = i
                logger.info(f"Executing step {i + 1}/{len(workflow.steps)}: {step.name}")

                result = await self._execute_step(step, execution.context)

                if step.output_key:
                    execution.results[step.output_key] = result
                    execution.context[step.output_key] = result

            execution.status = WorkflowStatus.COMPLETED
            execution.completed_at = datetime.utcnow()

        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            execution.status = WorkflowStatus.FAILED
            execution.errors.append({
                "step": execution.current_step,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
            execution.completed_at = datetime.utcnow()

        return execution

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
    ) -> Any:
        """Execute a single workflow step."""

        if step.type == StepType.AGENT:
            return await self._execute_agent_step(step, context)

        elif step.type == StepType.PARALLEL:
            return await self._execute_parallel_steps(step, context)

        elif step.type == StepType.CONDITIONAL:
            return await self._execute_conditional_step(step, context)

        elif step.type == StepType.TRANSFORM:
            return self._execute_transform_step(step, context)

        elif step.type == StepType.WAIT:
            await asyncio.sleep(step.config.get("seconds", 1))
            return {"waited": True}

        raise ValueError(f"Unknown step type: {step.type}")

    async def _execute_agent_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
    ) -> Any:
        """Execute an agent capability step."""
        if not step.agent_id or not step.capability:
            raise ValueError("Agent step requires agent_id and capability")

        # Build input from context using input_mapping
        input_data = {}
        for target_key, source_path in step.input_mapping.items():
            value = self._resolve_path(context, source_path)
            if value is not None:
                input_data[target_key] = value

        # Add any static config
        input_data.update(step.config.get("static_input", {}))

        # Execute agent
        response = await self._loader.execute_agent(
            agent_id=step.agent_id,
            capability=step.capability,
            payload=input_data,
        )

        if not response.success:
            raise RuntimeError(f"Agent execution failed: {response.error}")

        return response.data

    async def _execute_parallel_steps(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute multiple steps in parallel."""
        tasks = []
        for parallel_step in step.parallel_steps:
            task = asyncio.create_task(
                self._execute_step(parallel_step, context)
            )
            tasks.append((parallel_step.output_key or parallel_step.name, task))

        results = {}
        for key, task in tasks:
            try:
                results[key] = await task
            except Exception as e:
                results[key] = {"error": str(e)}

        return results

    async def _execute_conditional_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
    ) -> Any:
        """Execute a conditional step."""
        # Evaluate condition
        condition_value = self._resolve_path(context, step.condition or "")

        if condition_value:
            if step.if_true:
                return await self._execute_step(step.if_true, context)
        else:
            if step.if_false:
                return await self._execute_step(step.if_false, context)

        return None

    def _execute_transform_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
    ) -> Any:
        """Execute a data transformation step."""
        transform_type = step.config.get("transform_type", "identity")
        source = step.config.get("source", "")

        data = self._resolve_path(context, source)

        if transform_type == "identity":
            return data
        elif transform_type == "extract":
            key = step.config.get("key", "")
            return data.get(key) if isinstance(data, dict) else data
        elif transform_type == "merge":
            sources = step.config.get("sources", [])
            merged = {}
            for src in sources:
                src_data = self._resolve_path(context, src)
                if isinstance(src_data, dict):
                    merged.update(src_data)
            return merged

        return data

    def _resolve_path(self, context: Dict[str, Any], path: str) -> Any:
        """Resolve a dot-notation path in the context."""
        if not path:
            return None

        parts = path.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

        return value

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get a workflow execution by ID."""
        return self._executions.get(execution_id)

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[WorkflowStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List workflow executions with optional filters."""
        executions = self._executions.values()

        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]

        if status:
            executions = [e for e in executions if e.status == status]

        return [e.to_dict() for e in executions]


# Global engine instance
_engine: Optional[WorkflowEngine] = None


def get_workflow_engine() -> WorkflowEngine:
    """Get the global workflow engine instance."""
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
