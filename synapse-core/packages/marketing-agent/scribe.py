"""
The Scribe - Marketing Content Generation Agent
Handles brand voice consistency, content creation, and SEO optimization.
"""

import os
import json
import logging
from typing import Annotated, TypedDict, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


# --- State Definition ---
class ScribeState(TypedDict):
    """State for The Scribe agent."""

    messages: Annotated[list, add_messages]
    brand_voice: str
    content_type: str
    user_id: str
    thread_id: str


# --- Tools for The Scribe ---
@tool
def get_brand_voice(user_id: str) -> str:
    """
    Retrieve the brand voice guidelines for a user.

    Args:
        user_id: The user's unique identifier

    Returns:
        Brand voice guidelines as a string
    """
    # Placeholder - will integrate with database
    default_voice = {
        "tone": "professional yet approachable",
        "style": "clear and concise",
        "keywords": ["innovative", "reliable", "expert"],
        "avoid": ["jargon", "passive voice", "clichés"],
    }
    return json.dumps(default_voice)


@tool
def analyze_sentiment(text: str) -> dict:
    """
    Analyze the sentiment and tone of marketing content.

    Args:
        text: The text to analyze

    Returns:
        Sentiment analysis results
    """
    # Placeholder - will integrate with sentiment analysis
    return {
        "sentiment": "positive",
        "confidence": 0.85,
        "tone": "professional",
        "suggestions": [],
    }


@tool
def optimize_for_seo(content: str, keywords: list[str]) -> dict:
    """
    Optimize content for search engines.

    Args:
        content: The content to optimize
        keywords: Target keywords

    Returns:
        SEO optimization results and suggestions
    """
    word_count = len(content.split())
    keyword_density = {}
    content_lower = content.lower()

    for kw in keywords:
        count = content_lower.count(kw.lower())
        keyword_density[kw] = round((count / word_count) * 100, 2) if word_count > 0 else 0

    return {
        "word_count": word_count,
        "keyword_density": keyword_density,
        "readability_score": 75,  # Placeholder
        "suggestions": [
            "Consider adding more internal links",
            "Include a call-to-action",
        ],
    }


@tool
def generate_content_variations(content: str, count: int = 3) -> list[str]:
    """
    Generate variations of marketing content.

    Args:
        content: The original content
        count: Number of variations to generate

    Returns:
        List of content variations
    """
    # Placeholder - will use LLM for actual variations
    return [
        f"Variation 1: {content}",
        f"Variation 2 (shorter): {content[:len(content)//2]}...",
        f"Variation 3 (question): Did you know? {content}",
    ][:count]


# --- Agent Node Functions ---
def create_scribe_agent():
    """Create and return The Scribe agent graph."""

    # Initialize the LLM
    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
        temperature=0.7,
    )

    tools = [get_brand_voice, analyze_sentiment, optimize_for_seo, generate_content_variations]
    model_with_tools = model.bind_tools(tools)

    system_prompt = """You are The Scribe, an expert marketing content agent for Synapse Core.

Your responsibilities:
1. Generate high-quality marketing content that matches the brand voice
2. Ensure content is optimized for the target audience
3. Maintain consistency across all marketing materials
4. Provide SEO-optimized content when requested

You have access to tools for:
- Retrieving brand voice guidelines
- Analyzing sentiment and tone
- Optimizing content for SEO
- Generating content variations

Always start by checking the brand voice guidelines before creating content.
Provide clear, engaging, and professional marketing copy.

Format your responses as JSON when possible:
{
    "type": "content" | "analysis" | "suggestions",
    "content": "...",
    "metadata": {...}
}
"""

    def agent_node(state: ScribeState) -> dict:
        """Main agent decision node."""
        messages = state["messages"]

        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + list(messages)

        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: ScribeState) -> Literal["tools", END]:
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build the graph
    graph = StateGraph(ScribeState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")

    # Compile with memory
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# Create the agent app
scribe_agent_app = create_scribe_agent()


# --- Convenience Functions ---
def invoke_scribe(
    prompt: str,
    user_id: str,
    thread_id: str,
    brand_voice: str = "",
    content_type: str = "general",
) -> dict:
    """
    Convenience function to invoke The Scribe agent.

    Args:
        prompt: The user's request
        user_id: User identifier
        thread_id: Thread/conversation identifier
        brand_voice: Optional brand voice override
        content_type: Type of content to generate

    Returns:
        Agent response as a dictionary
    """
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    result = scribe_agent_app.invoke(
        {
            "messages": [HumanMessage(content=prompt)],
            "brand_voice": brand_voice,
            "content_type": content_type,
            "user_id": user_id,
            "thread_id": thread_id,
        },
        config=config,
    )

    last_message = result["messages"][-1]
    return {
        "response": last_message.content,
        "thread_id": thread_id,
        "agent": "scribe",
    }
