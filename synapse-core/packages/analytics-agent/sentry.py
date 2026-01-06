"""
The Sentry - Analytics and Monitoring Agent
Handles performance monitoring, metrics analysis, and anomaly detection.
"""

import os
import json
import logging
from typing import Annotated, TypedDict, Literal
from datetime import datetime, timedelta, UTC

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


# --- State Definition ---
class SentryState(TypedDict):
    """State for The Sentry agent."""

    messages: Annotated[list, add_messages]
    metrics_type: str
    time_range: str
    user_id: str
    thread_id: str


# --- Tools for The Sentry ---
@tool
def get_performance_metrics(user_id: str, time_range: str = "24h") -> dict:
    """
    Fetch performance metrics for a user's applications.

    Args:
        user_id: The user's unique identifier
        time_range: Time range for metrics (1h, 24h, 7d, 30d)

    Returns:
        Performance metrics data
    """
    # Placeholder - will integrate with actual monitoring
    return {
        "time_range": time_range,
        "page_load_time": {
            "avg_ms": 1250,
            "p50_ms": 980,
            "p95_ms": 2100,
            "p99_ms": 3500,
        },
        "api_response_time": {
            "avg_ms": 145,
            "p50_ms": 120,
            "p95_ms": 350,
            "p99_ms": 890,
        },
        "error_rate": 0.02,
        "uptime": 99.95,
        "requests_per_minute": 450,
    }


@tool
def detect_anomalies(metrics: dict) -> dict:
    """
    Detect anomalies in performance metrics.

    Args:
        metrics: Performance metrics to analyze

    Returns:
        Detected anomalies and severity
    """
    anomalies = []

    # Check for slow page loads
    if metrics.get("page_load_time", {}).get("p95_ms", 0) > 3000:
        anomalies.append({
            "type": "slow_page_load",
            "severity": "warning",
            "message": "P95 page load time exceeds 3 seconds",
            "recommendation": "Consider optimizing images and reducing JavaScript bundle size",
        })

    # Check error rate
    if metrics.get("error_rate", 0) > 0.05:
        anomalies.append({
            "type": "high_error_rate",
            "severity": "critical",
            "message": f"Error rate at {metrics.get('error_rate', 0) * 100:.1f}%",
            "recommendation": "Review recent deployments and check error logs",
        })

    return {
        "anomalies_detected": len(anomalies),
        "anomalies": anomalies,
        "health_score": max(0, 100 - len(anomalies) * 15),
    }


@tool
def analyze_traffic_trends(user_id: str, days: int = 7) -> dict:
    """
    Analyze traffic trends over time.

    Args:
        user_id: The user's unique identifier
        days: Number of days to analyze

    Returns:
        Traffic trend analysis
    """
    # Placeholder - will integrate with analytics
    return {
        "period_days": days,
        "total_visitors": 15420,
        "unique_visitors": 8930,
        "page_views": 42150,
        "bounce_rate": 0.35,
        "avg_session_duration_seconds": 185,
        "trend": {
            "visitors_change": 0.12,  # 12% increase
            "page_views_change": 0.08,
            "bounce_rate_change": -0.03,  # 3% decrease (good)
        },
        "top_pages": [
            {"path": "/", "views": 12500},
            {"path": "/products", "views": 8200},
            {"path": "/about", "views": 3100},
        ],
        "traffic_sources": {
            "organic": 0.45,
            "direct": 0.25,
            "referral": 0.18,
            "social": 0.12,
        },
    }


@tool
def generate_insights_report(metrics: dict, trends: dict) -> dict:
    """
    Generate actionable insights from metrics and trends.

    Args:
        metrics: Performance metrics
        trends: Traffic trend data

    Returns:
        Insights and recommendations
    """
    insights = []

    # Performance insights
    if metrics.get("page_load_time", {}).get("avg_ms", 0) > 2000:
        insights.append({
            "category": "performance",
            "insight": "Average page load time is above optimal threshold",
            "impact": "high",
            "action": "Implement lazy loading and optimize critical rendering path",
        })

    # Traffic insights
    if trends.get("trend", {}).get("visitors_change", 0) > 0.1:
        insights.append({
            "category": "growth",
            "insight": f"Traffic increased by {trends['trend']['visitors_change']*100:.0f}% this period",
            "impact": "positive",
            "action": "Scale infrastructure proactively to handle increased load",
        })

    if trends.get("bounce_rate", 1) > 0.5:
        insights.append({
            "category": "engagement",
            "insight": "Bounce rate is above 50%",
            "impact": "medium",
            "action": "Review landing page content and improve calls-to-action",
        })

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "insights_count": len(insights),
        "insights": insights,
        "summary": f"Found {len(insights)} actionable insights based on current data",
    }


@tool
def set_alert_threshold(metric_name: str, threshold: float, comparison: str = "gt") -> dict:
    """
    Configure an alert threshold for a metric.

    Args:
        metric_name: Name of the metric to monitor
        threshold: Threshold value
        comparison: Comparison type (gt, lt, eq, gte, lte)

    Returns:
        Alert configuration confirmation
    """
    return {
        "status": "configured",
        "alert": {
            "metric": metric_name,
            "threshold": threshold,
            "comparison": comparison,
            "notification_channels": ["email", "slack"],
        },
        "message": f"Alert configured: Notify when {metric_name} {comparison} {threshold}",
    }


# --- Agent Node Functions ---
def create_sentry_agent():
    """Create and return The Sentry agent graph."""

    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
        temperature=0.2,  # Low temperature for analytical accuracy
    )

    tools = [
        get_performance_metrics,
        detect_anomalies,
        analyze_traffic_trends,
        generate_insights_report,
        set_alert_threshold,
    ]
    model_with_tools = model.bind_tools(tools)

    system_prompt = """You are The Sentry, an expert analytics and monitoring agent for Synapse Core.

Your responsibilities:
1. Monitor application performance and health
2. Analyze traffic patterns and user behavior
3. Detect anomalies and potential issues
4. Generate actionable insights and recommendations
5. Configure alerts and notifications

You have access to tools for:
- Fetching performance metrics (page load, API response times, error rates)
- Detecting anomalies in metrics
- Analyzing traffic trends
- Generating insights reports
- Setting up alert thresholds

Analysis Guidelines:
- Always consider both short-term and long-term trends
- Prioritize critical issues that affect user experience
- Provide specific, actionable recommendations
- Use data to support your conclusions
- Consider the business context when making recommendations

Format your responses as JSON:
{
    "type": "analytics_report" | "insight" | "alert_config",
    "data": {...},
    "insights": [...],
    "recommendations": [...]
}

For questions or clarifications:
{
    "type": "text",
    "content": "your message"
}
"""

    def agent_node(state: SentryState) -> dict:
        """Main agent decision node."""
        messages = state["messages"]

        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=system_prompt)] + list(messages)

        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: SentryState) -> Literal["tools", END]:
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # Build the graph
    graph = StateGraph(SentryState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue)
    graph.add_edge("tools", "agent")

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


# Create the agent app
sentry_agent_app = create_sentry_agent()


# --- Convenience Functions ---
def invoke_sentry(
    prompt: str,
    user_id: str,
    thread_id: str,
    metrics_type: str = "all",
    time_range: str = "24h",
) -> dict:
    """
    Convenience function to invoke The Sentry agent.

    Args:
        prompt: The user's analytics request
        user_id: User identifier
        thread_id: Thread/conversation identifier
        metrics_type: Type of metrics to analyze
        time_range: Time range for analysis

    Returns:
        Agent response as a dictionary
    """
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    result = sentry_agent_app.invoke(
        {
            "messages": [HumanMessage(content=prompt)],
            "metrics_type": metrics_type,
            "time_range": time_range,
            "user_id": user_id,
            "thread_id": thread_id,
        },
        config=config,
    )

    last_message = result["messages"][-1]
    return {
        "response": last_message.content,
        "thread_id": thread_id,
        "agent": "sentry",
    }
