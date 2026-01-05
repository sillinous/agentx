"""
Spatial Agent - Generates detailed location descriptions and environmental designs.

Uses Claude 3 Haiku to create rich environmental specifications that maintain
consistency with the world configuration.
"""
import logging
from typing import Dict, Any
from anthropic import Anthropic

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SpatialAgent(BaseAgent):
    """
    Generates location and environment descriptions for worldbuilding.

    Creates detailed location descriptions including geography, landmarks,
    atmosphere, and map-worthy environmental specifications.
    """

    def __init__(self):
        super().__init__(agent_type='spatial')
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("SpatialAgent initialized without Anthropic API key")

    def _build_world_context(self, world_config: Dict[str, Any]) -> str:
        """
        Build world context string for location generation.

        Args:
            world_config: Dictionary with genre, tone, tech_level, etc.

        Returns:
            Formatted context string
        """
        context_parts = ["Generate a location description for a world with:"]

        if world_config:
            if world_config.get('genre'):
                context_parts.append(f"- Genre: {world_config['genre']}")
            if world_config.get('tone'):
                context_parts.append(f"- Tone: {world_config['tone']}")
            if world_config.get('tech_level'):
                context_parts.append(f"- Technology Level: {world_config['tech_level']}")
            if world_config.get('physics'):
                context_parts.append(f"- Physics: {world_config['physics']}")

        return "\n".join(context_parts)

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate location description based on input parameters.

        Args:
            input_data: Dictionary containing:
                - location_name: Name of the location
                - world_config: World configuration dict (optional)
                - type: Location type like 'city', 'wilderness', 'structure' (optional)
                - details: Additional details to include (optional)

        Returns:
            Dictionary containing:
                - location_name: Name of the location
                - description: Detailed description
                - landmarks: List of notable landmarks
                - atmosphere: Atmospheric description
                - map_layout: Layout description for mapping
        """
        if not self.client:
            # Mock mode for testing without API key
            logger.warning("SpatialAgent running in mock mode (no API key)")
            return {
                "location_name": input_data.get('location_name', 'Unknown Location'),
                "description": f"[MOCK] Description for: {input_data.get('location_name', 'Unknown')}",
                "landmarks": ["Mock Landmark 1", "Mock Landmark 2"],
                "atmosphere": "Mock atmospheric description",
                "map_layout": "Mock layout description"
            }

        location_name = input_data.get('location_name', 'Unnamed Location')
        world_config = input_data.get('world_config', {})
        location_type = input_data.get('type', 'location')
        details = input_data.get('details', '')

        # Build context from world config
        world_context = self._build_world_context(world_config)

        # Create the full prompt
        instruction = f"""{world_context}

Create a detailed description for this location:

**Name:** {location_name}
**Type:** {location_type}
{f"**Additional Details:** {details}" if details else ""}

Provide the following in your response:

1. **Overall Description** (2-3 paragraphs): Paint a vivid picture of the location
2. **Key Landmarks** (3-5 items): Notable features, buildings, or natural formations
3. **Atmosphere**: The mood, feeling, and sensory details (sounds, smells, lighting)
4. **Layout**: A description of the spatial arrangement suitable for creating a map

Be specific and detailed while maintaining consistency with the world's characteristics."""

        try:
            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2500,
                messages=[{
                    "role": "user",
                    "content": instruction
                }]
            )

            content = response.content[0].text

            # Parse the response (simple parsing - in production you might want structured output)
            result = {
                "location_name": location_name,
                "description": content,
                "landmarks": self._extract_landmarks(content),
                "atmosphere": self._extract_atmosphere(content),
                "map_layout": self._extract_layout(content),
                "model": "claude-3-haiku-20240307",
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens
            }

            return result

        except Exception as e:
            logger.error(f"SpatialAgent failed to generate location: {e}")
            raise

    def _extract_landmarks(self, content: str) -> list:
        """Extract landmarks from the generated content."""
        # Simple extraction - look for "Key Landmarks" section
        landmarks = []
        if "Key Landmarks" in content or "Landmarks" in content:
            lines = content.split('\n')
            in_landmarks = False
            for line in lines:
                if "landmark" in line.lower():
                    in_landmarks = True
                    continue
                if in_landmarks and line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                    landmarks.append(line.strip().lstrip('-•*123456789. '))
                elif in_landmarks and line.strip() and not line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                    break
        return landmarks[:5] if landmarks else ["See description for landmarks"]

    def _extract_atmosphere(self, content: str) -> str:
        """Extract atmosphere description from the generated content."""
        # Look for "Atmosphere" section
        if "Atmosphere" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "atmosphere" in line.lower():
                    # Get the next few lines
                    atmosphere_lines = []
                    for j in range(i+1, min(i+4, len(lines))):
                        if lines[j].strip() and not lines[j].strip().startswith('**'):
                            atmosphere_lines.append(lines[j].strip())
                    return ' '.join(atmosphere_lines) if atmosphere_lines else "See description"
        return "See description"

    def _extract_layout(self, content: str) -> str:
        """Extract layout description from the generated content."""
        # Look for "Layout" section
        if "Layout" in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "layout" in line.lower():
                    # Get the next few lines
                    layout_lines = []
                    for j in range(i+1, min(i+5, len(lines))):
                        if lines[j].strip() and not lines[j].strip().startswith('**'):
                            layout_lines.append(lines[j].strip())
                    return ' '.join(layout_lines) if layout_lines else "See description"
        return "See description"

    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence based on completeness of the location description.

        Args:
            result: The generated output

        Returns:
            Confidence score between 0.0 and 1.0
        """
        description = result.get('description', '')
        landmarks = result.get('landmarks', [])

        # Base confidence
        confidence = 0.8

        # Adjust based on content length
        if len(description) < 200:
            confidence -= 0.2  # Too short
        elif len(description) > 500:
            confidence += 0.1  # Good length

        # Check if landmarks were extracted
        if landmarks and len(landmarks) > 1 and landmarks[0] != "See description for landmarks":
            confidence += 0.1

        # Ensure confidence stays in valid range
        return max(0.0, min(1.0, confidence))
