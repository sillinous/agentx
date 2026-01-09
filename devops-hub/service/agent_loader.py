"""
Agent Loader - Dynamically loads and manages agent instances.
"""

from typing import Dict, Optional, Type
import logging

from built_in_agents.base import BaseAgent, AgentMessage, AgentContext, AgentResponse, MessageType

# Import all agent implementations
from built_in_agents.system.supervisor.agent import SupervisorAgent
from built_in_agents.system.router.agent import RouterAgent
from built_in_agents.system.registry.agent import RegistryAgent
from built_in_agents.system.monitor.agent import MonitorAgent
from built_in_agents.business.research.agent import ResearchAnalyzerAgent
from built_in_agents.business.data_processor.agent import DataProcessorAgent
from built_in_agents.business.finance.agent import FinanceAnalystAgent
from built_in_agents.business.project_manager.agent import ProjectManagerAgent
from built_in_agents.business.content_creator.agent import ContentCreatorAgent
from built_in_agents.utility.code_reviewer.agent import CodeReviewerAgent
from built_in_agents.utility.doc_generator.agent import DocumentationGeneratorAgent
from built_in_agents.utility.task_decomposer.agent import TaskDecomposerAgent
from built_in_agents.utility.error_handler.agent import ErrorHandlerAgent

logger = logging.getLogger(__name__)

# Agent class registry
AGENT_CLASSES: Dict[str, Type[BaseAgent]] = {
    "supervisor-agent": SupervisorAgent,
    "router-agent": RouterAgent,
    "registry-agent": RegistryAgent,
    "monitor-agent": MonitorAgent,
    "research-analyzer": ResearchAnalyzerAgent,
    "data-processor": DataProcessorAgent,
    "finance-analyst": FinanceAnalystAgent,
    "project-manager": ProjectManagerAgent,
    "content-creator": ContentCreatorAgent,
    "code-reviewer": CodeReviewerAgent,
    "documentation-generator": DocumentationGeneratorAgent,
    "task-decomposer": TaskDecomposerAgent,
    "error-handler": ErrorHandlerAgent,
}


class AgentLoader:
    """
    Manages agent instance lifecycle.

    Features:
    - Lazy instantiation of agents
    - Instance caching for reuse
    - Automatic agent startup
    """

    def __init__(self):
        self._instances: Dict[str, BaseAgent] = {}
        self._started: Dict[str, bool] = {}

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get or create an agent instance."""
        if agent_id not in AGENT_CLASSES:
            return None

        if agent_id not in self._instances:
            agent_class = AGENT_CLASSES[agent_id]
            self._instances[agent_id] = agent_class()
            self._started[agent_id] = False

        return self._instances[agent_id]

    async def ensure_started(self, agent_id: str) -> bool:
        """Ensure an agent is started."""
        agent = self.get_agent(agent_id)
        if not agent:
            return False

        if not self._started.get(agent_id):
            try:
                await agent.start()
                self._started[agent_id] = True
            except Exception as e:
                logger.error(f"Failed to start agent {agent_id}: {e}")
                return False

        return True

    async def execute_agent(
        self,
        agent_id: str,
        capability: str,
        payload: Dict,
        context: Optional[AgentContext] = None,
    ) -> AgentResponse:
        """Execute an agent capability."""
        # Ensure agent is loaded and started
        if not await self.ensure_started(agent_id):
            return AgentResponse.error_response(
                f"Agent {agent_id} not available",
                error_code="AGENT_NOT_AVAILABLE",
            )

        agent = self._instances[agent_id]
        context = context or AgentContext()

        # Create message
        message = AgentMessage(
            type=MessageType.REQUEST,
            sender="api-service",
            recipient=agent_id,
            capability=capability,
            payload=payload,
        )

        # Execute
        try:
            response = await agent.handle_message(message, context)
            return response
        except Exception as e:
            logger.exception(f"Error executing agent {agent_id}")
            return AgentResponse.error_response(
                str(e),
                error_code="EXECUTION_ERROR",
            )

    def get_agent_capabilities(self, agent_id: str) -> list:
        """Get capabilities for an agent."""
        agent = self.get_agent(agent_id)
        if not agent:
            return []
        return [c.name for c in agent.get_capabilities()]

    def get_agent_health(self, agent_id: str) -> Optional[Dict]:
        """Get health status for an agent."""
        agent = self.get_agent(agent_id)
        if not agent:
            return None
        return agent.get_health().to_dict()

    def list_available_agents(self) -> list:
        """List all available agent IDs."""
        return list(AGENT_CLASSES.keys())

    async def shutdown_all(self):
        """Shutdown all running agents."""
        for agent_id, agent in self._instances.items():
            if self._started.get(agent_id):
                try:
                    await agent.stop()
                except Exception as e:
                    logger.error(f"Error stopping agent {agent_id}: {e}")

        self._instances.clear()
        self._started.clear()


# Global loader instance
_loader: Optional[AgentLoader] = None


def get_loader() -> AgentLoader:
    """Get the global agent loader instance."""
    global _loader
    if _loader is None:
        _loader = AgentLoader()
    return _loader
