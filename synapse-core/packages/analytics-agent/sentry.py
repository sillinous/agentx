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

# In-memory metrics store for demo (in production, would connect to real monitoring)
_metrics_store: dict = {}


def _generate_realistic_metrics(user_id: str, time_range: str) -> dict:
    """Generate realistic metrics based on time range and simulated patterns."""
    import random
    from datetime import datetime, timedelta

    # Base metrics that vary by time of day and user activity
    base_load_time = 1200
    base_api_time = 140
    base_error_rate = 0.015
    base_requests = 400

    # Add some randomness for realism
    random.seed(hash(user_id + time_range + str(datetime.now().hour)))

    # Time-based variations (busier during business hours)
    hour = datetime.now().hour
    time_factor = 1.0 + 0.3 * (1 if 9 <= hour <= 17 else -0.2)

    # Generate metrics
    load_time_avg = int(base_load_time * (0.8 + random.random() * 0.4))
    api_time_avg = int(base_api_time * (0.8 + random.random() * 0.4))
    error_rate = round(base_error_rate * (0.5 + random.random()), 4)
    requests = int(base_requests * time_factor * (0.7 + random.random() * 0.6))

    return {
        "load_time_avg": load_time_avg,
        "load_time_p50": int(load_time_avg * 0.8),
        "load_time_p95": int(load_time_avg * 1.7),
        "load_time_p99": int(load_time_avg * 2.5),
        "api_time_avg": api_time_avg,
        "api_time_p50": int(api_time_avg * 0.85),
        "api_time_p95": int(api_time_avg * 2.5),
        "api_time_p99": int(api_time_avg * 5),
        "error_rate": error_rate,
        "requests_per_minute": requests,
    }


@tool
def get_performance_metrics(user_id: str, time_range: str = "24h") -> dict:
    """
    Fetch performance metrics for a user's applications.

    Args:
        user_id: The user's unique identifier
        time_range: Time range for metrics (1h, 24h, 7d, 30d)

    Returns:
        Comprehensive performance metrics data
    """
    # Generate realistic metrics
    metrics = _generate_realistic_metrics(user_id, time_range)

    # Calculate uptime based on error rate
    uptime = round(100 - (metrics["error_rate"] * 100), 2)

    # Time range multipliers for totals
    time_multipliers = {"1h": 60, "24h": 1440, "7d": 10080, "30d": 43200}
    multiplier = time_multipliers.get(time_range, 1440)

    return {
        "time_range": time_range,
        "collected_at": datetime.now(UTC).isoformat(),
        "page_load_time": {
            "avg_ms": metrics["load_time_avg"],
            "p50_ms": metrics["load_time_p50"],
            "p95_ms": metrics["load_time_p95"],
            "p99_ms": metrics["load_time_p99"],
            "trend": "stable" if metrics["load_time_avg"] < 1500 else "degraded",
        },
        "api_response_time": {
            "avg_ms": metrics["api_time_avg"],
            "p50_ms": metrics["api_time_p50"],
            "p95_ms": metrics["api_time_p95"],
            "p99_ms": metrics["api_time_p99"],
            "trend": "healthy" if metrics["api_time_avg"] < 200 else "needs_attention",
        },
        "error_rate": {
            "current": metrics["error_rate"],
            "percentage": f"{metrics['error_rate'] * 100:.2f}%",
            "status": "healthy" if metrics["error_rate"] < 0.02 else "warning" if metrics["error_rate"] < 0.05 else "critical",
        },
        "uptime": {
            "percentage": uptime,
            "status": "excellent" if uptime > 99.9 else "good" if uptime > 99 else "needs_improvement",
        },
        "traffic": {
            "requests_per_minute": metrics["requests_per_minute"],
            "total_requests": metrics["requests_per_minute"] * multiplier,
            "peak_rpm": int(metrics["requests_per_minute"] * 1.5),
        },
        "core_web_vitals": {
            "lcp_ms": metrics["load_time_avg"],  # Largest Contentful Paint
            "fid_ms": int(metrics["api_time_avg"] * 0.3),  # First Input Delay
            "cls": round(0.05 + (metrics["error_rate"] * 2), 3),  # Cumulative Layout Shift
            "status": "passing" if metrics["load_time_avg"] < 2500 else "needs_improvement",
        },
    }


@tool
def detect_anomalies(metrics: dict) -> dict:
    """
    Detect anomalies in performance metrics using statistical analysis.

    Args:
        metrics: Performance metrics to analyze

    Returns:
        Comprehensive anomaly detection results with severity and recommendations
    """
    anomalies = []
    warnings = []
    health_deductions = 0

    # Extract metrics with safe defaults
    page_load = metrics.get("page_load_time", {})
    api_response = metrics.get("api_response_time", {})
    error_info = metrics.get("error_rate", {})
    traffic = metrics.get("traffic", {})
    web_vitals = metrics.get("core_web_vitals", {})

    # Handle both old and new metric formats
    error_rate = error_info.get("current", error_info) if isinstance(error_info, dict) else error_info
    if isinstance(error_rate, str):
        error_rate = float(error_rate.replace("%", "")) / 100

    # 1. Page Load Time Analysis
    p95_load = page_load.get("p95_ms", 0)
    avg_load = page_load.get("avg_ms", 0)

    if p95_load > 4000:
        anomalies.append({
            "id": "PLT_CRITICAL",
            "type": "slow_page_load",
            "severity": "critical",
            "metric": "page_load_time.p95",
            "value": f"{p95_load}ms",
            "threshold": "4000ms",
            "message": "Critical: P95 page load time exceeds 4 seconds",
            "impact": "Users are likely abandoning your site due to slow load times",
            "recommendations": [
                "Implement code splitting to reduce initial bundle size",
                "Add lazy loading for images and below-fold content",
                "Enable server-side rendering for critical pages",
                "Review and optimize third-party scripts",
            ],
        })
        health_deductions += 25
    elif p95_load > 2500:
        warnings.append({
            "id": "PLT_WARNING",
            "type": "slow_page_load",
            "severity": "warning",
            "metric": "page_load_time.p95",
            "value": f"{p95_load}ms",
            "threshold": "2500ms",
            "message": "P95 page load time exceeds recommended threshold",
            "recommendations": [
                "Optimize and compress images",
                "Minimize render-blocking resources",
                "Consider implementing a CDN",
            ],
        })
        health_deductions += 10

    # 2. API Response Time Analysis
    p95_api = api_response.get("p95_ms", 0)
    avg_api = api_response.get("avg_ms", 0)

    if p95_api > 1000:
        anomalies.append({
            "id": "API_CRITICAL",
            "type": "slow_api_response",
            "severity": "critical",
            "metric": "api_response_time.p95",
            "value": f"{p95_api}ms",
            "threshold": "1000ms",
            "message": "API response times are critically slow",
            "impact": "User interactions feel sluggish, affecting engagement",
            "recommendations": [
                "Review database query performance",
                "Implement caching for frequently accessed data",
                "Consider horizontal scaling for high-traffic endpoints",
                "Profile backend code for bottlenecks",
            ],
        })
        health_deductions += 20
    elif p95_api > 500:
        warnings.append({
            "id": "API_WARNING",
            "type": "slow_api_response",
            "severity": "warning",
            "metric": "api_response_time.p95",
            "value": f"{p95_api}ms",
            "threshold": "500ms",
            "message": "API response times above optimal threshold",
            "recommendations": [
                "Add database indexes for common queries",
                "Implement response caching",
            ],
        })
        health_deductions += 8

    # 3. Error Rate Analysis
    if error_rate > 0.05:
        anomalies.append({
            "id": "ERR_CRITICAL",
            "type": "high_error_rate",
            "severity": "critical",
            "metric": "error_rate",
            "value": f"{error_rate * 100:.2f}%",
            "threshold": "5%",
            "message": f"Critical error rate detected: {error_rate * 100:.2f}%",
            "impact": "Significant number of users experiencing errors",
            "recommendations": [
                "Check recent deployments for breaking changes",
                "Review error logs for patterns",
                "Implement circuit breakers for failing services",
                "Set up real-time alerting for error spikes",
            ],
        })
        health_deductions += 30
    elif error_rate > 0.02:
        warnings.append({
            "id": "ERR_WARNING",
            "type": "elevated_error_rate",
            "severity": "warning",
            "metric": "error_rate",
            "value": f"{error_rate * 100:.2f}%",
            "threshold": "2%",
            "message": f"Error rate above normal: {error_rate * 100:.2f}%",
            "recommendations": [
                "Monitor error trends",
                "Review error logs for recurring issues",
            ],
        })
        health_deductions += 10

    # 4. Core Web Vitals Analysis
    lcp = web_vitals.get("lcp_ms", 0)
    cls = web_vitals.get("cls", 0)

    if lcp > 4000:
        warnings.append({
            "id": "LCP_POOR",
            "type": "poor_lcp",
            "severity": "warning",
            "metric": "core_web_vitals.lcp",
            "value": f"{lcp}ms",
            "threshold": "2500ms (good), 4000ms (poor)",
            "message": "Largest Contentful Paint is in 'poor' range",
            "recommendations": [
                "Optimize the largest visible content element",
                "Preload critical resources",
            ],
        })
        health_deductions += 10

    if cls > 0.25:
        warnings.append({
            "id": "CLS_POOR",
            "type": "poor_cls",
            "severity": "warning",
            "metric": "core_web_vitals.cls",
            "value": str(cls),
            "threshold": "0.1 (good), 0.25 (poor)",
            "message": "Cumulative Layout Shift indicates poor visual stability",
            "recommendations": [
                "Set explicit dimensions for images and embeds",
                "Reserve space for dynamic content",
            ],
        })
        health_deductions += 8

    # 5. Traffic Anomalies
    rpm = traffic.get("requests_per_minute", 0)
    if rpm > 1000:
        warnings.append({
            "id": "TRAFFIC_HIGH",
            "type": "high_traffic",
            "severity": "info",
            "metric": "traffic.requests_per_minute",
            "value": str(rpm),
            "message": "Higher than usual traffic detected",
            "recommendations": [
                "Ensure auto-scaling is configured",
                "Monitor resource utilization",
            ],
        })

    # Calculate health score
    health_score = max(0, 100 - health_deductions)

    return {
        "analysis_timestamp": datetime.now(UTC).isoformat(),
        "anomalies_detected": len(anomalies),
        "warnings_detected": len(warnings),
        "anomalies": anomalies,
        "warnings": warnings,
        "health_score": health_score,
        "health_status": (
            "critical" if health_score < 50 else
            "degraded" if health_score < 75 else
            "healthy" if health_score < 90 else
            "excellent"
        ),
        "summary": {
            "critical_issues": len([a for a in anomalies if a.get("severity") == "critical"]),
            "warnings": len(warnings),
            "total_recommendations": sum(len(a.get("recommendations", [])) for a in anomalies + warnings),
        },
    }


@tool
def analyze_traffic_trends(user_id: str, days: int = 7) -> dict:
    """
    Analyze traffic trends over time with detailed insights.

    Args:
        user_id: The user's unique identifier
        days: Number of days to analyze

    Returns:
        Comprehensive traffic trend analysis with actionable insights
    """
    import random

    # Seed for consistent but varied results per user
    random.seed(hash(user_id + str(days)))

    # Generate realistic base metrics
    base_daily_visitors = 2000 + random.randint(-500, 500)
    total_visitors = base_daily_visitors * days + random.randint(-1000, 2000)
    unique_ratio = 0.55 + random.random() * 0.15
    unique_visitors = int(total_visitors * unique_ratio)
    pages_per_session = 2.5 + random.random() * 1.5
    page_views = int(total_visitors * pages_per_session)

    # Calculate trends (compare to previous period)
    visitors_change = round(-0.05 + random.random() * 0.25, 3)
    views_change = round(-0.03 + random.random() * 0.20, 3)
    bounce_change = round(-0.08 + random.random() * 0.10, 3)

    # Bounce rate between 25-55%
    bounce_rate = round(0.25 + random.random() * 0.30, 3)

    # Session duration between 90-300 seconds
    avg_session = 90 + random.randint(0, 210)

    # Generate daily breakdown
    daily_data = []
    for i in range(days):
        day_factor = 0.7 + random.random() * 0.6  # Daily variation
        daily_data.append({
            "day": i + 1,
            "visitors": int(base_daily_visitors * day_factor),
            "page_views": int(base_daily_visitors * day_factor * pages_per_session),
            "bounce_rate": round(bounce_rate + (random.random() - 0.5) * 0.1, 3),
        })

    # Peak hours analysis
    peak_hours = sorted(
        [{"hour": h, "traffic_share": round(0.02 + random.random() * 0.08, 3)}
         for h in range(24)],
        key=lambda x: x["traffic_share"],
        reverse=True
    )[:5]

    # Geographic distribution
    geo_distribution = {
        "United States": round(0.35 + random.random() * 0.15, 2),
        "United Kingdom": round(0.08 + random.random() * 0.07, 2),
        "Germany": round(0.05 + random.random() * 0.05, 2),
        "Canada": round(0.04 + random.random() * 0.04, 2),
        "Other": 0,  # Will be calculated
    }
    geo_distribution["Other"] = round(1 - sum(list(geo_distribution.values())[:-1]), 2)

    # Device breakdown
    device_breakdown = {
        "mobile": round(0.55 + random.random() * 0.15, 2),
        "desktop": round(0.30 + random.random() * 0.10, 2),
        "tablet": 0,
    }
    device_breakdown["tablet"] = round(1 - device_breakdown["mobile"] - device_breakdown["desktop"], 2)

    # Generate insights
    insights = []

    if visitors_change > 0.10:
        insights.append({
            "type": "positive",
            "metric": "visitors",
            "message": f"Traffic increased by {visitors_change * 100:.1f}% compared to previous period",
            "recommendation": "Consider scaling infrastructure to handle increased load",
        })
    elif visitors_change < -0.05:
        insights.append({
            "type": "negative",
            "metric": "visitors",
            "message": f"Traffic decreased by {abs(visitors_change) * 100:.1f}%",
            "recommendation": "Review marketing campaigns and SEO strategy",
        })

    if bounce_rate > 0.50:
        insights.append({
            "type": "warning",
            "metric": "bounce_rate",
            "message": f"High bounce rate at {bounce_rate * 100:.1f}%",
            "recommendation": "Improve landing page content and loading speed",
        })

    if device_breakdown["mobile"] > 0.60:
        insights.append({
            "type": "info",
            "metric": "devices",
            "message": f"Mobile traffic dominates at {device_breakdown['mobile'] * 100:.0f}%",
            "recommendation": "Prioritize mobile UX and performance optimization",
        })

    if avg_session < 120:
        insights.append({
            "type": "warning",
            "metric": "engagement",
            "message": f"Low average session duration ({avg_session}s)",
            "recommendation": "Add engaging content and clear CTAs to increase time on site",
        })

    return {
        "period_days": days,
        "analysis_date": datetime.now(UTC).isoformat(),
        "summary": {
            "total_visitors": total_visitors,
            "unique_visitors": unique_visitors,
            "page_views": page_views,
            "bounce_rate": bounce_rate,
            "bounce_rate_display": f"{bounce_rate * 100:.1f}%",
            "avg_session_duration_seconds": avg_session,
            "avg_session_display": f"{avg_session // 60}m {avg_session % 60}s",
            "pages_per_session": round(pages_per_session, 2),
        },
        "trends": {
            "visitors_change": visitors_change,
            "visitors_change_display": f"{'+' if visitors_change > 0 else ''}{visitors_change * 100:.1f}%",
            "page_views_change": views_change,
            "page_views_change_display": f"{'+' if views_change > 0 else ''}{views_change * 100:.1f}%",
            "bounce_rate_change": bounce_change,
            "bounce_rate_change_display": f"{'+' if bounce_change > 0 else ''}{bounce_change * 100:.1f}%",
            "trend_direction": "up" if visitors_change > 0.02 else "down" if visitors_change < -0.02 else "stable",
        },
        "daily_breakdown": daily_data,
        "peak_hours": peak_hours,
        "top_pages": [
            {"path": "/", "views": int(page_views * 0.30), "avg_time_seconds": 45},
            {"path": "/products", "views": int(page_views * 0.20), "avg_time_seconds": 120},
            {"path": "/pricing", "views": int(page_views * 0.12), "avg_time_seconds": 90},
            {"path": "/about", "views": int(page_views * 0.08), "avg_time_seconds": 60},
            {"path": "/blog", "views": int(page_views * 0.07), "avg_time_seconds": 180},
        ],
        "traffic_sources": {
            "organic_search": round(0.40 + random.random() * 0.15, 2),
            "direct": round(0.20 + random.random() * 0.10, 2),
            "referral": round(0.12 + random.random() * 0.08, 2),
            "social": round(0.10 + random.random() * 0.08, 2),
            "email": round(0.05 + random.random() * 0.05, 2),
            "paid": round(0.03 + random.random() * 0.05, 2),
        },
        "geography": geo_distribution,
        "devices": device_breakdown,
        "insights": insights,
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
        insights.append(
            {
                "category": "performance",
                "insight": "Average page load time is above optimal threshold",
                "impact": "high",
                "action": "Implement lazy loading and optimize critical rendering path",
            }
        )

    # Traffic insights
    if trends.get("trend", {}).get("visitors_change", 0) > 0.1:
        insights.append(
            {
                "category": "growth",
                "insight": f"Traffic increased by {trends['trend']['visitors_change']*100:.0f}% this period",
                "impact": "positive",
                "action": "Scale infrastructure proactively to handle increased load",
            }
        )

    if trends.get("bounce_rate", 1) > 0.5:
        insights.append(
            {
                "category": "engagement",
                "insight": "Bounce rate is above 50%",
                "impact": "medium",
                "action": "Review landing page content and improve calls-to-action",
            }
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "insights_count": len(insights),
        "insights": insights,
        "summary": f"Found {len(insights)} actionable insights based on current data",
    }


@tool
def set_alert_threshold(
    metric_name: str, threshold: float, comparison: str = "gt"
) -> dict:
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
