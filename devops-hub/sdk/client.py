"""
DevOps Hub SDK Client - Python client for interacting with the Agent Library Service.

Usage:
    # Synchronous client
    from sdk import AgentServiceClient

    client = AgentServiceClient("http://localhost:8100")
    agents = client.list_agents()
    result = client.execute_agent("research-analyzer", "market-analysis", {"market": "AI"})

    # Async client
    from sdk import AsyncAgentServiceClient

    async with AsyncAgentServiceClient("http://localhost:8100") as client:
        agents = await client.list_agents()
        result = await client.execute_agent("research-analyzer", "market-analysis", {"market": "AI"})
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import httpx


@dataclass
class Agent:
    """Represents an agent from the registry."""
    id: str
    name: str
    version: str
    status: str
    domain: str
    type: str
    description: str
    capabilities: List[str]
    protocols: List[str] = None
    implementations: Dict[str, str] = None
    documentation: str = None
    performance: Dict[str, Any] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Agent":
        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            status=data["status"],
            domain=data["domain"],
            type=data["type"],
            description=data["description"],
            capabilities=data["capabilities"],
            protocols=data.get("protocols"),
            implementations=data.get("implementations"),
            documentation=data.get("documentation"),
            performance=data.get("performance"),
        )


@dataclass
class ExecutionResult:
    """Result of an agent execution."""
    agent_id: str
    status: str
    output: Optional[Dict[str, Any]]
    error: Optional[str]
    execution_time_ms: float
    timestamp: str

    @property
    def success(self) -> bool:
        return self.status == "success"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionResult":
        return cls(
            agent_id=data["agent_id"],
            status=data["status"],
            output=data.get("output"),
            error=data.get("error"),
            execution_time_ms=data["execution_time_ms"],
            timestamp=data["timestamp"],
        )


@dataclass
class WorkflowExecution:
    """Result of a workflow execution."""
    id: str
    workflow_id: str
    workflow_name: str
    status: str
    current_step: int
    context: Dict[str, Any]
    results: Dict[str, Any]
    errors: List[Dict[str, Any]]
    started_at: Optional[str]
    completed_at: Optional[str]

    @property
    def success(self) -> bool:
        return self.status == "completed"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowExecution":
        return cls(
            id=data["id"],
            workflow_id=data["workflow_id"],
            workflow_name=data["workflow_name"],
            status=data["status"],
            current_step=data["current_step"],
            context=data["context"],
            results=data["results"],
            errors=data["errors"],
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
        )


class AgentServiceError(Exception):
    """Exception raised when API calls fail."""

    def __init__(self, message: str, status_code: int = None, detail: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class AgentServiceClient:
    """
    Synchronous client for the Agent Library Service.

    Example:
        client = AgentServiceClient("http://localhost:8100")
        agents = client.list_agents()
        result = client.execute_agent("research-analyzer", "market-analysis", {"market": "AI"})
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the client.

        Args:
            base_url: Base URL of the Agent Library Service (e.g., "http://localhost:8100")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def close(self):
        """Close the client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request."""
        url = f"{self.base_url}{path}"
        response = self._client.request(method, url, **kwargs)

        if response.status_code >= 400:
            detail = None
            try:
                detail = response.json().get("detail")
            except Exception:
                pass
            raise AgentServiceError(
                f"API request failed: {response.status_code}",
                status_code=response.status_code,
                detail=detail,
            )

        return response.json()

    # Health & Status

    def health(self) -> Dict[str, Any]:
        """Check service health."""
        return self._request("GET", "/health")

    def statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return self._request("GET", "/statistics")

    # Agent Discovery

    def list_agents(self, status: str = None) -> List[Agent]:
        """List all agents, optionally filtered by status."""
        params = {}
        if status:
            params["status"] = status
        data = self._request("GET", "/agents", params=params)
        return [Agent.from_dict(a) for a in data]

    def get_agent(self, agent_id: str) -> Agent:
        """Get details for a specific agent."""
        data = self._request("GET", f"/agents/{agent_id}")
        return Agent.from_dict(data)

    def discover_agents(
        self,
        domain: str = None,
        capability: str = None,
        status: str = "production",
        agent_type: str = None,
    ) -> List[Agent]:
        """Discover agents matching criteria."""
        params = {}
        if domain:
            params["domain"] = domain
        if capability:
            params["capability"] = capability
        if status:
            params["status"] = status
        if agent_type:
            params["agent_type"] = agent_type

        data = self._request("GET", "/agents/discover", params=params)
        return [Agent.from_dict(a) for a in data["agents"]]

    def get_capabilities(self) -> List[str]:
        """Get all available capabilities."""
        data = self._request("GET", "/capabilities")
        return data["capabilities"]

    def get_domains(self) -> List[str]:
        """Get all domains."""
        data = self._request("GET", "/domains")
        return data["domains"]

    # Agent Execution

    def execute_agent(
        self,
        agent_id: str,
        capability: str,
        input_data: Dict[str, Any] = None,
        timeout_seconds: int = 300,
    ) -> ExecutionResult:
        """
        Execute an agent capability.

        Args:
            agent_id: ID of the agent to execute
            capability: Capability to invoke
            input_data: Input data for the capability
            timeout_seconds: Execution timeout

        Returns:
            ExecutionResult with the output
        """
        payload = {
            "capability": capability,
            "input_data": input_data or {},
            "timeout_seconds": timeout_seconds,
        }
        data = self._request("POST", f"/agents/{agent_id}/execute", json=payload)
        return ExecutionResult.from_dict(data)

    def validate_agent(self, agent_id: str) -> Dict[str, Any]:
        """Validate an agent against the 8 principles."""
        return self._request("POST", f"/agents/{agent_id}/validate")

    # Workflows

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List available workflows."""
        data = self._request("GET", "/workflows")
        return data["workflows"]

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow details."""
        return self._request("GET", f"/workflows/{workflow_id}")

    def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any] = None,
    ) -> WorkflowExecution:
        """Execute a workflow."""
        data = self._request(
            "POST",
            f"/workflows/{workflow_id}/execute",
            json=input_data or {},
        )
        return WorkflowExecution.from_dict(data)

    def create_workflow(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """Create a custom workflow."""
        payload = {
            "name": name,
            "description": description,
            "version": version,
            "steps": steps,
        }
        return self._request("POST", "/workflows", json=payload)

    def list_executions(
        self,
        workflow_id: str = None,
        status: str = None,
    ) -> List[Dict[str, Any]]:
        """List workflow executions."""
        params = {}
        if workflow_id:
            params["workflow_id"] = workflow_id
        if status:
            params["status"] = status
        data = self._request("GET", "/workflow-executions", params=params)
        return data["executions"]

    def get_execution(self, execution_id: str) -> WorkflowExecution:
        """Get workflow execution details."""
        data = self._request("GET", f"/workflow-executions/{execution_id}")
        return WorkflowExecution.from_dict(data)

    # Events

    def get_events(
        self,
        event_type: str = None,
        source: str = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get event history."""
        params = {"limit": limit}
        if event_type:
            params["event_type"] = event_type
        if source:
            params["source"] = source
        data = self._request("GET", "/events", params=params)
        return data["events"]

    def publish_event(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        correlation_id: str = None,
    ) -> Dict[str, Any]:
        """Publish an event."""
        payload = {
            "type": event_type,
            "source": source,
            "data": data,
        }
        if correlation_id:
            payload["correlation_id"] = correlation_id
        return self._request("POST", "/events", json=payload)


class AsyncAgentServiceClient:
    """
    Asynchronous client for the Agent Library Service.

    Example:
        async with AsyncAgentServiceClient("http://localhost:8100") as client:
            agents = await client.list_agents()
            result = await client.execute_agent("research-analyzer", "market-analysis", {"market": "AI"})
    """

    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the async client.

        Args:
            base_url: Base URL of the Agent Library Service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an async HTTP request."""
        url = f"{self.base_url}{path}"
        response = await self._client.request(method, url, **kwargs)

        if response.status_code >= 400:
            detail = None
            try:
                detail = response.json().get("detail")
            except Exception:
                pass
            raise AgentServiceError(
                f"API request failed: {response.status_code}",
                status_code=response.status_code,
                detail=detail,
            )

        return response.json()

    # Health & Status

    async def health(self) -> Dict[str, Any]:
        """Check service health."""
        return await self._request("GET", "/health")

    async def statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return await self._request("GET", "/statistics")

    # Agent Discovery

    async def list_agents(self, status: str = None) -> List[Agent]:
        """List all agents."""
        params = {}
        if status:
            params["status"] = status
        data = await self._request("GET", "/agents", params=params)
        return [Agent.from_dict(a) for a in data]

    async def get_agent(self, agent_id: str) -> Agent:
        """Get agent details."""
        data = await self._request("GET", f"/agents/{agent_id}")
        return Agent.from_dict(data)

    async def discover_agents(
        self,
        domain: str = None,
        capability: str = None,
        status: str = "production",
        agent_type: str = None,
    ) -> List[Agent]:
        """Discover agents matching criteria."""
        params = {}
        if domain:
            params["domain"] = domain
        if capability:
            params["capability"] = capability
        if status:
            params["status"] = status
        if agent_type:
            params["agent_type"] = agent_type

        data = await self._request("GET", "/agents/discover", params=params)
        return [Agent.from_dict(a) for a in data["agents"]]

    async def get_capabilities(self) -> List[str]:
        """Get all capabilities."""
        data = await self._request("GET", "/capabilities")
        return data["capabilities"]

    async def get_domains(self) -> List[str]:
        """Get all domains."""
        data = await self._request("GET", "/domains")
        return data["domains"]

    # Agent Execution

    async def execute_agent(
        self,
        agent_id: str,
        capability: str,
        input_data: Dict[str, Any] = None,
        timeout_seconds: int = 300,
    ) -> ExecutionResult:
        """Execute an agent capability."""
        payload = {
            "capability": capability,
            "input_data": input_data or {},
            "timeout_seconds": timeout_seconds,
        }
        data = await self._request("POST", f"/agents/{agent_id}/execute", json=payload)
        return ExecutionResult.from_dict(data)

    async def validate_agent(self, agent_id: str) -> Dict[str, Any]:
        """Validate an agent."""
        return await self._request("POST", f"/agents/{agent_id}/validate")

    # Workflows

    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List workflows."""
        data = await self._request("GET", "/workflows")
        return data["workflows"]

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow details."""
        return await self._request("GET", f"/workflows/{workflow_id}")

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any] = None,
    ) -> WorkflowExecution:
        """Execute a workflow."""
        data = await self._request(
            "POST",
            f"/workflows/{workflow_id}/execute",
            json=input_data or {},
        )
        return WorkflowExecution.from_dict(data)

    async def create_workflow(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        version: str = "1.0.0",
    ) -> Dict[str, Any]:
        """Create a custom workflow."""
        payload = {
            "name": name,
            "description": description,
            "version": version,
            "steps": steps,
        }
        return await self._request("POST", "/workflows", json=payload)

    async def list_executions(
        self,
        workflow_id: str = None,
        status: str = None,
    ) -> List[Dict[str, Any]]:
        """List workflow executions."""
        params = {}
        if workflow_id:
            params["workflow_id"] = workflow_id
        if status:
            params["status"] = status
        data = await self._request("GET", "/workflow-executions", params=params)
        return data["executions"]

    async def get_execution(self, execution_id: str) -> WorkflowExecution:
        """Get execution details."""
        data = await self._request("GET", f"/workflow-executions/{execution_id}")
        return WorkflowExecution.from_dict(data)

    # Events

    async def get_events(
        self,
        event_type: str = None,
        source: str = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get event history."""
        params = {"limit": limit}
        if event_type:
            params["event_type"] = event_type
        if source:
            params["source"] = source
        data = await self._request("GET", "/events", params=params)
        return data["events"]

    async def publish_event(
        self,
        event_type: str,
        source: str,
        data: Dict[str, Any],
        correlation_id: str = None,
    ) -> Dict[str, Any]:
        """Publish an event."""
        payload = {
            "type": event_type,
            "source": source,
            "data": data,
        }
        if correlation_id:
            payload["correlation_id"] = correlation_id
        return await self._request("POST", "/events", json=payload)
