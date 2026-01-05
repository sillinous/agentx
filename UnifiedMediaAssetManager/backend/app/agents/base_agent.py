"""
Base Agent class for all AI agents in UnifiedMediaAssetManager.

Provides a standard interface for agent implementation with job tracking,
confidence scoring, and error handling.
"""
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents.

    All agents must implement the process() method which contains
    the core agent logic for their specific task.
    """

    def __init__(self, agent_type: str):
        """
        Initialize the agent.

        Args:
            agent_type: Type identifier for this agent (e.g., 'narrative', 'spatial')
        """
        self.agent_type = agent_type
        self.api_key = os.getenv('ANTHROPIC_API_KEY')

        if not self.api_key:
            logger.warning(f"{agent_type} agent initialized without ANTHROPIC_API_KEY")

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process agent task and return result.

        This method must be implemented by all agent subclasses.

        Args:
            input_data: Dictionary containing input parameters for the agent

        Returns:
            Dictionary containing:
                - content: The generated content
                - type: Type of content generated
                - metadata: Additional metadata (optional)
        """
        pass

    def calculate_confidence(self, result: Any) -> float:
        """
        Calculate confidence score for the agent's output.

        Override in subclasses for agent-specific confidence calculation.

        Args:
            result: The output from the agent

        Returns:
            Float between 0.0 and 1.0 indicating confidence level
        """
        # Default implementation returns high confidence
        # Subclasses should override with more sophisticated logic
        return 0.9

    def should_require_human_review(self, confidence_score: float) -> bool:
        """
        Determine if human review is required based on confidence score.

        Args:
            confidence_score: Confidence score from 0.0 to 1.0

        Returns:
            True if human review is required, False otherwise
        """
        # Require human review if confidence is below 75%
        return confidence_score < 0.75

    async def execute(self, job_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent job with full tracking and error handling.

        This method wraps the process() method with standard job management logic.

        Args:
            job_id: Unique identifier for this job
            input_data: Input parameters for the agent

        Returns:
            Dictionary containing:
                - success: Boolean indicating if job succeeded
                - output_data: Result from process() if successful
                - confidence_score: Confidence score
                - human_review_required: Boolean flag
                - error: Error message if failed
        """
        try:
            logger.info(f"[{self.agent_type}] Starting job {job_id}")

            # Call the agent-specific processing logic
            output_data = await self.process(input_data)

            # Calculate confidence score
            confidence_score = self.calculate_confidence(output_data)

            # Determine if human review is needed
            human_review_required = self.should_require_human_review(confidence_score)

            logger.info(
                f"[{self.agent_type}] Job {job_id} completed. "
                f"Confidence: {confidence_score:.2f}, "
                f"Review required: {human_review_required}"
            )

            return {
                'success': True,
                'output_data': output_data,
                'confidence_score': confidence_score,
                'human_review_required': human_review_required,
                'error': None
            }

        except Exception as e:
            logger.error(f"[{self.agent_type}] Job {job_id} failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'output_data': None,
                'confidence_score': 0.0,
                'human_review_required': True,
                'error': str(e)
            }
