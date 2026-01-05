"""
VideoStrategyAgent - Translates user intent into video generation parameters.

Uses mood classification and camera movement matrices to enrich prompts
with cinematic vocabulary and generate multiple creative variations.
"""
import logging
from typing import Dict, Any, List
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class VideoStrategyAgent(BaseAgent):
    """
    Generates video strategy and parameters based on user intent.

    Translates abstract user requirements (mood, tone) into concrete video
    generation parameters (camera movements, lighting, aspect ratios).
    """

    # Mood classification matrix
    MOOD_MATRIX = {
        "high_energy": {
            "range": (75, 100),
            "cameras": [
                "fpv_drone",
                "crash_zoom_in",
                "whip_pan_right",
                "handheld_heavy",
                "bullet_time"
            ],
            "lighting": [
                "high_contrast",
                "neon_glow",
                "strobe_effect",
                "harsh_shadows"
            ],
            "keywords": [
                "dynamic",
                "explosive",
                "intense",
                "fast-paced",
                "aggressive",
                "energetic"
            ],
            "color_grade": [
                "vibrant",
                "saturated",
                "punchy"
            ]
        },
        "luxury_reveal": {
            "range": (50, 75),
            "cameras": [
                "dolly_slow",
                "crane_up",
                "pan_slow",
                "orbit_smooth",
                "push_in_elegant"
            ],
            "lighting": [
                "golden_hour",
                "soft_key",
                "rim_lighting",
                "three_point"
            ],
            "keywords": [
                "elegant",
                "sophisticated",
                "premium",
                "refined",
                "graceful",
                "polished"
            ],
            "color_grade": [
                "cinematic",
                "warm_tones",
                "rich_colors"
            ]
        },
        "intimate_story": {
            "range": (25, 50),
            "cameras": [
                "static_focus",
                "handheld_subtle",
                "dolly_zoom",
                "slow_push",
                "rack_focus"
            ],
            "lighting": [
                "natural",
                "warm_ambient",
                "soft_window",
                "candlelight"
            ],
            "keywords": [
                "personal",
                "emotional",
                "authentic",
                "intimate",
                "heartfelt",
                "sincere"
            ],
            "color_grade": [
                "natural",
                "muted_tones",
                "soft_palette"
            ]
        },
        "surreal_trip": {
            "range": (0, 25),
            "cameras": [
                "bullet_time",
                "spiral_zoom",
                "through_object",
                "inverted_gravity",
                "fish_eye"
            ],
            "lighting": [
                "neon_noir",
                "volumetric",
                "colored_gels",
                "mystical_glow"
            ],
            "keywords": [
                "dreamlike",
                "abstract",
                "otherworldly",
                "psychedelic",
                "surreal",
                "hypnotic"
            ],
            "color_grade": [
                "experimental",
                "high_saturation",
                "split_toning"
            ]
        }
    }

    # Platform-specific configurations
    PLATFORM_CONFIGS = {
        "tiktok": {
            "aspect_ratio": "9:16",
            "mood_boost": 20,  # TikTok favors high energy
            "duration_default": 15,
            "keywords": ["trending", "viral", "catchy"]
        },
        "youtube": {
            "aspect_ratio": "16:9",
            "mood_boost": 0,
            "duration_default": 30,
            "keywords": ["cinematic", "professional", "engaging"]
        },
        "instagram": {
            "aspect_ratio": "4:5",
            "mood_boost": 10,
            "duration_default": 15,
            "keywords": ["aesthetic", "stylish", "beautiful"]
        }
    }

    def __init__(self):
        super().__init__(agent_type='video_strategy')

    def _classify_mood(self, mood_slider: int) -> str:
        """
        Classify mood based on slider value (0-100).

        Args:
            mood_slider: Integer from 0-100

        Returns:
            Mood category string
        """
        for mood_name, config in self.MOOD_MATRIX.items():
            min_val, max_val = config["range"]
            if min_val <= mood_slider <= max_val:
                return mood_name

        # Fallback to intimate_story for out-of-range values
        return "intimate_story"

    def _enrich_prompt(
        self,
        base_prompt: str,
        mood_category: str,
        camera_movement: str
    ) -> str:
        """
        Enrich prompt with cinematic vocabulary.

        Args:
            base_prompt: User's original prompt
            mood_category: Classified mood category
            camera_movement: Selected camera movement

        Returns:
            Enriched prompt string
        """
        mood_config = self.MOOD_MATRIX[mood_category]

        # Select enrichment elements
        keyword = mood_config["keywords"][0]
        lighting = mood_config["lighting"][0]
        color_grade = mood_config["color_grade"][0]

        # Construct enriched prompt
        enriched = f"{base_prompt}, {keyword} atmosphere, {camera_movement} camera movement, {lighting} lighting, {color_grade} color grading"

        return enriched

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate video strategy variations based on user input.

        Args:
            input_data: Dictionary containing:
                - prompt: Base description for the video
                - mood_slider: Integer 0-100 indicating mood
                - aspect_ratio: Optional aspect ratio (default: '16:9')
                - platform: Optional platform ('tiktok', 'youtube', 'instagram')
                - num_variations: Number of variations to generate (default: 3)

        Returns:
            Dictionary containing:
                - mood_category: Classified mood
                - variations: List of video parameter dicts
                - platform_optimized: Boolean indicating if platform-specific
        """
        prompt = input_data.get('prompt', '')
        mood_slider = input_data.get('mood_slider', 50)
        aspect_ratio = input_data.get('aspect_ratio', '16:9')
        platform = input_data.get('platform', None)
        num_variations = input_data.get('num_variations', 3)

        if not prompt:
            raise ValueError("Prompt is required for video strategy")

        # Apply platform-specific adjustments if platform specified
        if platform and platform in self.PLATFORM_CONFIGS:
            platform_config = self.PLATFORM_CONFIGS[platform]
            mood_slider = min(100, mood_slider + platform_config["mood_boost"])
            aspect_ratio = platform_config["aspect_ratio"]
            duration_default = platform_config["duration_default"]
            platform_keywords = platform_config["keywords"]
            platform_optimized = True
        else:
            duration_default = 5
            platform_keywords = []
            platform_optimized = False

        # Classify mood
        mood_category = self._classify_mood(mood_slider)
        mood_config = self.MOOD_MATRIX[mood_category]

        logger.info(
            f"VideoStrategyAgent: Classified mood '{mood_category}' "
            f"from slider value {mood_slider}"
        )

        # Generate variations
        variations = []
        camera_movements = mood_config["cameras"][:num_variations]

        for i, camera_movement in enumerate(camera_movements):
            enriched_prompt = self._enrich_prompt(prompt, mood_category, camera_movement)

            # Add platform keywords if applicable
            if platform_keywords:
                enriched_prompt += f", {', '.join(platform_keywords)}"

            variation = {
                "id": f"variation_{i+1}",
                "prompt": enriched_prompt,
                "camera_movement": camera_movement,
                "aspect_ratio": aspect_ratio,
                "duration": duration_default,
                "mood_category": mood_category,
                "lighting": mood_config["lighting"][i % len(mood_config["lighting"])],
                "color_grade": mood_config["color_grade"][i % len(mood_config["color_grade"])],
                "metadata": {
                    "original_prompt": prompt,
                    "mood_slider": mood_slider,
                    "platform": platform
                }
            }

            variations.append(variation)

        result = {
            "mood_category": mood_category,
            "mood_slider": mood_slider,
            "variations": variations,
            "platform": platform,
            "platform_optimized": platform_optimized,
            "aspect_ratio": aspect_ratio
        }

        logger.info(
            f"VideoStrategyAgent: Generated {len(variations)} variations "
            f"for mood '{mood_category}'"
        )

        return result

    def calculate_confidence(self, result: Dict[str, Any]) -> float:
        """
        Calculate confidence based on strategy completeness.

        Args:
            result: The generated strategy

        Returns:
            Confidence score between 0.0 and 1.0
        """
        variations = result.get('variations', [])

        # Base confidence
        confidence = 0.85

        # Higher confidence if multiple variations generated
        if len(variations) >= 3:
            confidence += 0.1

        # Higher confidence if platform-optimized
        if result.get('platform_optimized'):
            confidence += 0.05

        # Ensure confidence stays in valid range
        return max(0.0, min(1.0, confidence))
