"""
Context Builder Service

Builds rich AI context from universe world configuration for consistent content generation.
"""
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
import logging

from ..models.database import (
    UniverseDB,
    WorldConfigDB,
    ElementDB,
    EntityTraitDB,
    TimelineEventDB
)

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds AI context from universe world configuration.

    This service gathers all world-building information (genre, physics, magic system,
    key entities, timeline) and formats it for AI agent consumption.
    """

    def __init__(self, db: Session):
        self.db = db

    def build_world_context(self, universe_id: UUID, max_entities: int = 10) -> Dict[str, Any]:
        """
        Gathers all world-building information for AI context.

        Args:
            universe_id: UUID of the universe
            max_entities: Maximum number of key entities to include

        Returns:
            Dictionary with world configuration, key entities, and timeline summary
        """
        try:
            # Get world configuration
            world_config = self._get_world_config(universe_id)

            # Get key entities (most recently updated, with traits)
            entities = self._get_key_entities(universe_id, limit=max_entities)

            # Get timeline summary (recent events)
            timeline = self._get_timeline_context(universe_id, limit=5)

            context = {
                "world_config": world_config,
                "key_entities": entities,
                "timeline_summary": timeline,
            }

            logger.info(f"Built world context for universe {universe_id}: "
                       f"{len(entities)} entities, {len(timeline)} timeline events")

            return context

        except Exception as e:
            logger.error(f"Error building world context for universe {universe_id}: {e}")
            return {
                "world_config": {},
                "key_entities": [],
                "timeline_summary": []
            }

    def build_prompt_context(self, universe_id: UUID) -> str:
        """
        Builds a formatted text prompt context for AI agents.

        This converts the structured world context into a natural language
        prompt that can be prepended to AI generation requests.

        Returns:
            Formatted string with world context
        """
        context = self.build_world_context(universe_id)

        if not context["world_config"]:
            return ""

        world_config = context["world_config"]
        prompt_parts = []

        # World configuration section
        prompt_parts.append("## World Context\n")

        if world_config.get("genre"):
            prompt_parts.append(f"**Genre**: {world_config['genre']}")

        if world_config.get("tone"):
            prompt_parts.append(f"**Tone**: {world_config['tone']}")

        if world_config.get("physics"):
            prompt_parts.append(f"**Physics**: {world_config['physics']}")

        if world_config.get("magic_system"):
            prompt_parts.append(f"**Magic System**: {world_config['magic_system']}")

        if world_config.get("tech_level"):
            prompt_parts.append(f"**Tech Level**: {world_config['tech_level']}")

        # Visual style section
        if world_config.get("art_style_notes") or world_config.get("color_palette"):
            prompt_parts.append("\n### Visual Style")

            if world_config.get("art_style_notes"):
                prompt_parts.append(f"**Art Style**: {world_config['art_style_notes']}")

            if world_config.get("color_palette"):
                palette_str = ", ".join([
                    f"{k}: {v}" for k, v in world_config["color_palette"].items()
                ])
                prompt_parts.append(f"**Color Palette**: {palette_str}")

        # Key entities section
        if context["key_entities"]:
            prompt_parts.append("\n### Key Entities")
            for entity in context["key_entities"][:5]:  # Limit to 5 for prompt brevity
                entity_line = f"- **{entity['name']}** ({entity['type']}"
                if entity.get("subtype"):
                    entity_line += f" - {entity['subtype']}"
                entity_line += ")"

                if entity.get("description"):
                    entity_line += f": {entity['description']}"

                prompt_parts.append(entity_line)

        # Timeline context section
        if context["timeline_summary"]:
            prompt_parts.append("\n### Recent Events")
            for event in context["timeline_summary"][:3]:  # Limit to 3 most recent
                event_line = f"- **{event['title']}**"
                if event.get("significance"):
                    event_line += f" ({event['significance']})"
                prompt_parts.append(event_line)

        prompt_parts.append("\n---\n")
        return "\n".join(prompt_parts)

    def _get_world_config(self, universe_id: UUID) -> Dict[str, Any]:
        """Get world configuration for universe"""
        config = self.db.query(WorldConfigDB).filter(
            WorldConfigDB.universe_id == str(universe_id)
        ).first()

        if not config:
            logger.warning(f"No world config found for universe {universe_id}")
            return {}

        return {
            "genre": config.genre,
            "physics": config.physics,
            "magic_system": config.magic_system,
            "tech_level": config.tech_level,
            "tone": config.tone,
            "color_palette": config.color_palette,
            "art_style_notes": config.art_style_notes,
            "reference_images": config.reference_images
        }

    def _get_key_entities(self, universe_id: UUID, limit: int = 10) -> List[Dict[str, Any]]:
        """Get key entities with their traits"""
        elements = self.db.query(ElementDB).filter(
            ElementDB.universe_id == str(universe_id)
        ).order_by(ElementDB.id.desc()).limit(limit).all()

        entities = []
        for element in elements:
            # Get AI-visible traits
            traits = self.db.query(EntityTraitDB).filter(
                EntityTraitDB.element_id == str(element.id),
                EntityTraitDB.is_ai_visible == True
            ).all()

            traits_dict = {
                trait.trait_key: trait.trait_value
                for trait in traits
            }

            entity_data = {
                "id": str(element.id),
                "name": element.name,
                "type": element.element_type,
                "subtype": element.entity_subtype,
                "traits": traits_dict
            }

            # Add description if available from traits
            if "description" in traits_dict:
                entity_data["description"] = traits_dict["description"]

            entities.append(entity_data)

        return entities

    def _get_timeline_context(self, universe_id: UUID, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent timeline events"""
        events = self.db.query(TimelineEventDB).filter(
            TimelineEventDB.universe_id == str(universe_id)
        ).order_by(TimelineEventDB.event_timestamp.desc()).limit(limit).all()

        timeline = []
        for event in events:
            timeline.append({
                "id": str(event.id),
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "significance": event.significance,
                "timestamp": event.event_timestamp.isoformat() if event.event_timestamp else None
            })

        return timeline

    def get_entity_context(self, element_id: UUID) -> Dict[str, Any]:
        """
        Get detailed context for a specific entity.

        Useful when generating content focused on a particular entity.
        """
        element = self.db.query(ElementDB).filter(
            ElementDB.id == str(element_id)
        ).first()

        if not element:
            logger.warning(f"Element {element_id} not found")
            return {}

        # Get all traits
        traits = self.db.query(EntityTraitDB).filter(
            EntityTraitDB.element_id == str(element_id)
        ).all()

        traits_by_category = {}
        for trait in traits:
            category = trait.trait_category or "general"
            if category not in traits_by_category:
                traits_by_category[category] = {}
            traits_by_category[category][trait.trait_key] = trait.trait_value

        return {
            "id": str(element.id),
            "name": element.name,
            "type": element.element_type,
            "subtype": element.entity_subtype,
            "traits_by_category": traits_by_category,
            "universe_id": str(element.universe_id)
        }


# Singleton instance getter
def get_context_builder(db: Session) -> ContextBuilder:
    """Get a ContextBuilder instance"""
    return ContextBuilder(db)
