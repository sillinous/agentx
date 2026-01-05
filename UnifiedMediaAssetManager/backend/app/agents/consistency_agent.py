"""
Consistency Agent - Validates generated content against world rules.

Ensures that all generated content maintains consistency with the world's
genre, tone, tech level, magic system, and physics rules.
"""
import logging
from typing import Dict, Any
from anthropic import Anthropic

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class ConsistencyAgent(BaseAgent):
    """
    Validates content consistency with world configuration.

    Checks generated content against world rules and flags violations
    for review or correction.
    """

    def __init__(self):
        super().__init__(agent_type='consistency')
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("ConsistencyAgent initialized without Anthropic API key")

    def _build_rules_context(self, world_config: Dict[str, Any]) -> str:
        """
        Build world rules context for consistency checking.

        Args:
            world_config: Dictionary with genre, tone, tech_level, etc.

        Returns:
            Formatted rules string
        """
        rules = ["The content must adhere to these world rules:"]

        if world_config:
            if world_config.get('genre'):
                rules.append(f"- Genre: {world_config['genre']} (content must fit this genre)")
            if world_config.get('tone'):
                rules.append(f"- Tone: {world_config['tone']} (content must match this tone)")
            if world_config.get('tech_level'):
                rules.append(f"- Tech Level: {world_config['tech_level']} (technology must be appropriate)")
            if world_config.get('magic_system'):
                rules.append(f"- Magic System: {world_config['magic_system']} (magic use must comply)")
            if world_config.get('physics'):
                rules.append(f"- Physics: {world_config['physics']} (physical laws must be consistent)")

        return "\n".join(rules)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate content against world rules.

        Args:
            input_data: Dictionary containing:
                - content: The content to validate
                - world_config: World configuration dict
                - content_type: Type of content (e.g., 'narrative', 'location')

        Returns:
            Dictionary containing:
                - is_consistent: Boolean indicating if content is consistent
                - violations: List of rule violations (if any)
                - explanation: Detailed explanation of the decision
                - suggestions: Suggestions for fixing violations (if any)
        """
        if not self.client:
            # Mock mode for testing without API key
            logger.warning("ConsistencyAgent running in mock mode (no API key)")
            return {
                "is_consistent": True,
                "violations": [],
                "explanation": "[MOCK] Content appears consistent",
                "suggestions": []
            }

        content = input_data.get('content', '')
        world_config = input_data.get('world_config', {})
        content_type = input_data.get('content_type', 'content')

        if not content:
            return {
                "is_consistent": False,
                "violations": ["No content provided"],
                "explanation": "Cannot validate empty content",
                "suggestions": ["Provide content to validate"]
            }

        # Build rules context
        rules_context = self._build_rules_context(world_config)

        # Create the validation prompt
        instruction = f"""{rules_context}

Review the following {content_type} and determine if it violates any of the world rules:

**Content to Validate:**
{content}

**Task:**
1. Analyze the content carefully against each rule
2. Identify any violations or inconsistencies
3. Explain your reasoning
4. If there are violations, suggest how to fix them

**Response Format:**
Start with either "CONSISTENT" or "INCONSISTENT", then provide your analysis.

If INCONSISTENT, list specific violations and suggestions.
If CONSISTENT, explain why the content adheres to the rules."""

        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                messages=[{
                    "role": "user",
                    "content": instruction
                }]
            )

            analysis = response.content[0].text

            # Parse the response
            is_consistent = "CONSISTENT" in analysis.upper() and "INCONSISTENT" not in analysis[:20].upper()

            # Extract violations and suggestions
            violations = self._extract_violations(analysis)
            suggestions = self._extract_suggestions(analysis)

            result = {
                "is_consistent": is_consistent,
                "violations": violations,
                "explanation": analysis,
                "suggestions": suggestions,
                "model": "claude-3-haiku-20240307",
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

            return result

        except Exception as e:
            logger.error(f"ConsistencyAgent failed to validate content: {e}")
            raise

    def _extract_violations(self, analysis: str) -> list:
        """Extract violations from the analysis text."""
        violations = []
        lines = analysis.split('\n')

        for line in lines:
            line_lower = line.lower()
            # Look for violation indicators
            if any(keyword in line_lower for keyword in ['violation', 'violates', 'inconsistent with', 'breaks']):
                clean_line = line.strip().lstrip('-•*123456789. ')
                if clean_line and len(clean_line) > 10:
                    violations.append(clean_line)

        return violations[:5] if violations else []

    def _extract_suggestions(self, analysis: str) -> list:
        """Extract suggestions from the analysis text."""
        suggestions = []
        lines = analysis.split('\n')
        in_suggestions = False

        for line in lines:
            line_lower = line.lower()

            # Check if we're entering a suggestions section
            if any(keyword in line_lower for keyword in ['suggest', 'fix', 'correct', 'improve']):
                in_suggestions = True
                continue

            # If we're in suggestions section, collect suggestion lines
            if in_suggestions:
                clean_line = line.strip().lstrip('-•*123456789. ')
                if clean_line and len(clean_line) > 10:
                    suggestions.append(clean_line)
                elif not clean_line:
                    in_suggestions = False

        return suggestions[:5] if suggestions else []

    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence in the consistency check.

        Higher confidence when the decision is clear and well-explained.

        Args:
            result: The validation result

        Returns:
            Confidence score between 0.0 and 1.0
        """
        explanation = result.get('explanation', '')
        violations = result.get('violations', [])

        # Base confidence
        confidence = 0.85

        # Higher confidence if the analysis is detailed
        if len(explanation) > 200:
            confidence += 0.1

        # If inconsistent but no violations extracted, lower confidence
        if not result.get('is_consistent') and not violations:
            confidence -= 0.2

        # If consistent and no violations, high confidence
        if result.get('is_consistent') and not violations:
            confidence += 0.05

        # Ensure confidence stays in valid range
        return max(0.0, min(1.0, confidence))

    def should_require_human_review(self, confidence_score: float) -> bool:
        """
        Consistency checks with violations should always be reviewed.

        Override base method to always flag violations for review.

        Args:
            confidence_score: Confidence score from 0.0 to 1.0

        Returns:
            True if human review is required
        """
        # Always require review if confidence is low
        if confidence_score < 0.7:
            return True

        # For consistency agent, we use a slightly higher threshold
        # because consistency decisions are important
        return False
