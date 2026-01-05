"""
Narrative Agent - Generates compelling narrative scenes based on story context.

Uses Claude 3 Haiku for fast, cost-effective narrative generation with
world configuration consistency.
"""
import logging
from typing import Dict, Any
from anthropic import Anthropic

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class NarrativeAgent(BaseAgent):
    """
    Generates narrative scenes and video prompts based on story context.

    Maintains consistency with world configuration (genre, tone, tech level, etc.)
    and generates both narrative text and video prompts.
    """

    def __init__(self):
        super().__init__(agent_type='narrative')
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("NarrativeAgent initialized without Anthropic API key")

    def _build_context(self, world_config: Dict[str, Any], characters: list) -> str:
        """
        Build context string from world configuration and characters.

        Args:
            world_config: Dictionary with genre, tone, tech_level, etc.
            characters: List of character dictionaries

        Returns:
            Formatted context string for the LLM
        """
        context_parts = ["You are a narrative generator for a story world with the following characteristics:"]

        if world_config:
            if world_config.get('genre'):
                context_parts.append(f"- Genre: {world_config['genre']}")
            if world_config.get('tone'):
                context_parts.append(f"- Tone: {world_config['tone']}")
            if world_config.get('tech_level'):
                context_parts.append(f"- Tech Level: {world_config['tech_level']}")
            if world_config.get('magic_system'):
                context_parts.append(f"- Magic System: {world_config['magic_system']}")
            if world_config.get('physics'):
                context_parts.append(f"- Physics: {world_config['physics']}")

        if characters:
            context_parts.append("\nRelevant Characters:")
            for char in characters:
                char_desc = f"- {char.get('name', 'Unknown')}"
                if char.get('description'):
                    char_desc += f": {char['description']}"
                context_parts.append(char_desc)

        return "\n".join(context_parts)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate narrative content based on input parameters.

        Args:
            input_data: Dictionary containing:
                - prompt: User's narrative request
                - world_config: World configuration dict (optional)
                - characters: List of character dicts (optional)
                - type: 'narrative' or 'video_prompt' (default: 'narrative')

        Returns:
            Dictionary containing:
                - type: Type of content generated
                - content: The generated narrative or prompt
                - model: Model used for generation
                - tokens_used: Token count (if available)
        """
        if not self.client:
            # Mock mode for testing without API key
            logger.warning("NarrativeAgent running in mock mode (no API key)")
            return {
                "type": input_data.get('type', 'narrative'),
                "content": f"[MOCK] Narrative for: {input_data.get('prompt', 'No prompt')}",
                "model": "mock",
                "tokens_used": 0
            }

        prompt = input_data.get('prompt', '')
        world_config = input_data.get('world_config', {})
        characters = input_data.get('characters', [])
        request_type = input_data.get('type', 'narrative')

        # Build context from world config and characters
        context = self._build_context(world_config, characters)

        # Create the full prompt
        if request_type == 'video_prompt':
            instruction = (
                f"{context}\n\n"
                f"Generate a detailed video prompt for: {prompt}\n\n"
                f"The prompt should describe visual scenes, camera movements, "
                f"lighting, and atmosphere that match the world's {world_config.get('genre', 'style')} genre "
                f"and {world_config.get('tone', 'mood')} tone."
            )
        else:
            instruction = (
                f"{context}\n\n"
                f"Generate a compelling narrative scene for: {prompt}\n\n"
                f"The scene should be 300-1000 words and maintain consistency "
                f"with the world's characteristics."
            )

        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": instruction
                }]
            )

            content = response.content[0].text

            return {
                "type": request_type,
                "content": content,
                "model": "claude-3-haiku-20240307",
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

        except Exception as e:
            logger.error(f"NarrativeAgent failed to generate content: {e}")
            raise

    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence based on content length and completeness.

        Args:
            result: The generated output

        Returns:
            Confidence score between 0.0 and 1.0
        """
        content = result.get('content', '')

        # Base confidence
        confidence = 0.8

        # Adjust based on content length
        if len(content) < 100:
            confidence -= 0.2  # Very short content
        elif len(content) > 500:
            confidence += 0.1  # Good length content

        # Check if it seems complete (ends with punctuation)
        if content.strip() and content.strip()[-1] in '.!?"':
            confidence += 0.05

        # Ensure confidence stays in valid range
        return max(0.0, min(1.0, confidence))
