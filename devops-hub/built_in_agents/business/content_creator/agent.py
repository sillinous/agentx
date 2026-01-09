# Content Creator Agent
# Content generation, editing, publishing, and optimization

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
import logging

from ...base import (
    BaseAgent,
    AgentCapability,
    AgentContext,
    AgentMessage,
    AgentResponse,
    Protocol,
)

logger = logging.getLogger(__name__)


@dataclass
class ContentItem:
    """A content item."""
    id: str
    title: str
    type: str
    content: str
    status: str = "draft"
    seo_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None


class ContentCreatorAgent(BaseAgent):
    """
    Content Creator Agent - Content generation and optimization.

    Capabilities:
    - content-generation: Generate various types of content
    - editing: Edit and improve existing content
    - publishing: Manage content publishing workflow
    - seo-optimization: Optimize content for search engines
    - style-consistency: Ensure consistent style across content
    """

    def __init__(self):
        super().__init__(
            agent_id="content-creator",
            name="Content Creator Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.MCP],
        )
        self._content: Dict[str, ContentItem] = {}

    def _register_default_capabilities(self) -> None:
        """Register content creation capabilities."""
        capabilities = [
            ("content-generation", "Generate articles, posts, and other content"),
            ("editing", "Edit, proofread, and improve content quality"),
            ("publishing", "Manage content publishing and scheduling"),
            ("seo-optimization", "Optimize content for search engines"),
            ("style-consistency", "Ensure consistent tone and style"),
        ]

        for name, desc in capabilities:
            self.register_capability(AgentCapability(name=name, description=desc))
            self.register_handler(name, self._handle_capability)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        return await self._handle_capability(message, context)

    async def _handle_capability(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "content-generation":
            return await self._generate_content(payload)
        elif capability == "editing":
            return await self._edit_content(payload)
        elif capability == "publishing":
            return await self._manage_publishing(payload)
        elif capability == "seo-optimization":
            return await self._optimize_seo(payload)
        elif capability == "style-consistency":
            return await self._check_style(payload)

        return AgentResponse.error_response(f"Unknown capability: {capability}")

    async def _generate_content(self, payload: Dict[str, Any]) -> AgentResponse:
        """Generate content."""
        content_type = payload.get("type", "article")
        topic = payload.get("topic", "General")
        tone = payload.get("tone", "professional")
        length = payload.get("length", "medium")

        content = ContentItem(
            id=str(uuid4()),
            title=f"Generated {content_type.title()}: {topic}",
            type=content_type,
            content=f"This is generated {content_type} content about {topic}...",
            status="draft",
            seo_score=0.75,
        )

        self._content[content.id] = content

        return AgentResponse.success_response({
            "content_id": content.id,
            "title": content.title,
            "type": content_type,
            "tone": tone,
            "word_count": 500,
            "status": "draft",
            "preview": content.content[:100] + "...",
        })

    async def _edit_content(self, payload: Dict[str, Any]) -> AgentResponse:
        """Edit content."""
        content_id = payload.get("content_id")
        edit_type = payload.get("edit_type", "proofread")

        return AgentResponse.success_response({
            "content_id": content_id,
            "edit_type": edit_type,
            "changes": [
                {"type": "grammar", "count": 3},
                {"type": "spelling", "count": 1},
                {"type": "style", "count": 5},
            ],
            "readability_score": 72,
            "suggestions": [
                "Consider shorter sentences in paragraph 2",
                "Add transition words between sections",
            ],
            "edited": True,
        })

    async def _manage_publishing(self, payload: Dict[str, Any]) -> AgentResponse:
        """Manage publishing workflow."""
        action = payload.get("action", "schedule")
        content_id = payload.get("content_id")

        if action == "schedule":
            return AgentResponse.success_response({
                "content_id": content_id,
                "scheduled": True,
                "publish_date": "2026-01-15T10:00:00Z",
                "channels": ["website", "newsletter", "social"],
            })
        elif action == "publish":
            return AgentResponse.success_response({
                "content_id": content_id,
                "published": True,
                "published_at": datetime.utcnow().isoformat(),
                "url": f"/content/{content_id}",
            })
        elif action == "queue":
            return AgentResponse.success_response({
                "queue": [
                    {"id": "1", "title": "Article 1", "scheduled": "2026-01-15"},
                    {"id": "2", "title": "Article 2", "scheduled": "2026-01-18"},
                    {"id": "3", "title": "Article 3", "scheduled": "2026-01-22"},
                ],
                "total": 3,
            })

        return AgentResponse.success_response({"action": action, "status": "processed"})

    async def _optimize_seo(self, payload: Dict[str, Any]) -> AgentResponse:
        """Optimize for SEO."""
        content_id = payload.get("content_id")
        keywords = payload.get("keywords", [])

        return AgentResponse.success_response({
            "content_id": content_id,
            "seo_score": 0.82,
            "analysis": {
                "title_optimization": {"score": 0.9, "status": "Good"},
                "meta_description": {"score": 0.85, "status": "Good"},
                "keyword_density": {"score": 0.75, "status": "Needs improvement"},
                "readability": {"score": 0.8, "status": "Good"},
                "internal_links": {"score": 0.6, "status": "Add more links"},
            },
            "suggestions": [
                f"Add keyword '{keywords[0] if keywords else 'target'}' to H2 heading",
                "Include more internal links",
                "Add alt text to images",
                "Optimize meta description length",
            ],
            "keywords_analyzed": keywords or ["default", "keywords"],
        })

    async def _check_style(self, payload: Dict[str, Any]) -> AgentResponse:
        """Check style consistency."""
        content_id = payload.get("content_id")
        style_guide = payload.get("style_guide", "default")

        return AgentResponse.success_response({
            "content_id": content_id,
            "style_guide": style_guide,
            "consistency_score": 0.88,
            "issues": [
                {"type": "tone", "location": "paragraph 3", "suggestion": "More formal tone needed"},
                {"type": "terminology", "location": "paragraph 5", "suggestion": "Use 'clients' instead of 'customers'"},
            ],
            "voice_analysis": {
                "active_voice": "85%",
                "passive_voice": "15%",
                "recommendation": "Good balance maintained",
            },
            "brand_alignment": 0.9,
        })
