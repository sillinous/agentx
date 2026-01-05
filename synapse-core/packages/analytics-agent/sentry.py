import logging
from typing import List, TypedDict, Annotated, Dict, Any
from langchain_core.messages import AnyMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from datetime import datetime, timedelta
import json
import random

# --- Logger Configuration ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logHandler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logHandler.setFormatter(formatter)
    logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


# --- Agent State ---
class SentryState(TypedDict):
    messages: Annotated[List[AnyMessage], lambda x, y: x + y]


# --- Tools for The Sentry ---


@tool
def fetch_performance_metrics(time_range: str = "24h") -> str:
    """
    Fetches key performance metrics for the specified time range.
    Returns metrics including page views, conversion rate, bounce rate, and average session duration.

    Args:
        time_range: Time range for metrics (e.g., "24h", "7d", "30d")
    """
    logger.info(f"TOOL: Fetching performance metrics for time range: {time_range}")

    # Simulated metrics (in production, would query actual analytics database)
    metrics = {
        "time_range": time_range,
        "page_views": random.randint(1000, 10000),
        "unique_visitors": random.randint(500, 5000),
        "conversion_rate": round(random.uniform(2.0, 8.0), 2),
        "bounce_rate": round(random.uniform(30.0, 60.0), 2),
        "avg_session_duration": f"{random.randint(2, 8)}m {random.randint(0, 59)}s",
        "revenue": round(random.uniform(1000, 50000), 2),
        "top_pages": [
            {"path": "/", "views": random.randint(100, 1000)},
            {"path": "/products", "views": random.randint(50, 800)},
            {"path": "/about", "views": random.randint(30, 500)},
        ],
    }

    result = f"""
Performance Metrics ({time_range}):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Traffic:
  • Page Views: {metrics['page_views']:,}
  • Unique Visitors: {metrics['unique_visitors']:,}

💰 Revenue & Conversions:
  • Conversion Rate: {metrics['conversion_rate']}%
  • Total Revenue: ${metrics['revenue']:,.2f}

⏱️ Engagement:
  • Bounce Rate: {metrics['bounce_rate']}%
  • Avg Session Duration: {metrics['avg_session_duration']}

🔝 Top Pages:
"""
    for page in metrics['top_pages']:
        result += f"  • {page['path']}: {page['views']:,} views\n"

    logger.info("Performance metrics fetched", extra=metrics)
    return result


@tool
def detect_anomalies(metric_name: str, threshold: float = 2.0) -> str:
    """
    Detects anomalies in specified metrics using statistical analysis.

    Args:
        metric_name: The metric to analyze (e.g., "traffic", "conversion_rate", "revenue")
        threshold: Standard deviation threshold for anomaly detection
    """
    logger.info(f"TOOL: Detecting anomalies for metric: {metric_name}, threshold: {threshold}")

    # Simulated anomaly detection
    anomalies_detected = random.choice([True, False])

    if not anomalies_detected:
        return f"✓ No anomalies detected for '{metric_name}' (within {threshold}σ threshold)"

    # Generate simulated anomaly report
    severity = random.choice(["minor", "moderate", "critical"])
    change_pct = random.uniform(-50, 50)

    report = f"""
⚠️ ANOMALY DETECTED: {metric_name}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Severity: {severity.upper()}
Change: {change_pct:+.1f}% from baseline
Detected: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Analysis:
- Current value deviates {threshold}+ standard deviations from historical average
- This pattern started approximately {random.randint(1, 48)} hours ago
- {'Immediate action recommended' if severity == 'critical' else 'Monitor closely'}

Recommendations:
- Review recent changes to website/marketing campaigns
- Check for technical issues or outages
- Analyze traffic sources for unusual patterns
"""

    logger.info(
        "Anomaly detection complete",
        extra={"metric": metric_name, "anomaly_detected": True, "severity": severity}
    )
    return report


@tool
def analyze_user_behavior(segment: str = "all") -> str:
    """
    Analyzes user behavior patterns for specified user segment.

    Args:
        segment: User segment to analyze (e.g., "all", "new", "returning", "high_value")
    """
    logger.info(f"TOOL: Analyzing user behavior for segment: {segment}")

    behaviors = {
        "segment": segment,
        "total_users": random.randint(100, 5000),
        "avg_pages_per_session": round(random.uniform(2.0, 8.0), 1),
        "most_common_path": "Home → Products → Checkout",
        "drop_off_points": [
            {"page": "Checkout", "rate": round(random.uniform(15, 40), 1)},
            {"page": "Product Details", "rate": round(random.uniform(10, 25), 1)},
        ],
        "device_breakdown": {
            "mobile": round(random.uniform(40, 70), 1),
            "desktop": round(random.uniform(20, 40), 1),
            "tablet": round(random.uniform(5, 15), 1),
        },
    }

    result = f"""
User Behavior Analysis - {segment.title()} Segment:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 Total Users: {behaviors['total_users']:,}

📱 Device Breakdown:
  • Mobile: {behaviors['device_breakdown']['mobile']}%
  • Desktop: {behaviors['device_breakdown']['desktop']}%
  • Tablet: {behaviors['device_breakdown']['tablet']}%

🛤️ User Journey:
  • Avg Pages/Session: {behaviors['avg_pages_per_session']}
  • Most Common Path: {behaviors['most_common_path']}

⚠️ Drop-off Points:
"""
    for point in behaviors['drop_off_points']:
        result += f"  • {point['page']}: {point['rate']}% drop-off\n"

    logger.info("User behavior analysis complete", extra=behaviors)
    return result


@tool
def generate_optimization_recommendations(focus_area: str = "general") -> str:
    """
    Generates data-driven optimization recommendations based on current metrics.

    Args:
        focus_area: Area to focus on (e.g., "general", "conversion", "engagement", "performance")
    """
    logger.info(f"TOOL: Generating recommendations for focus area: {focus_area}")

    recommendations = {
        "conversion": [
            "Add social proof elements (testimonials, reviews) above the fold",
            "Simplify checkout process - reduce from 4 steps to 2",
            "Implement exit-intent popups with special offers",
            "A/B test call-to-action button colors and copy",
        ],
        "engagement": [
            "Add interactive content (quizzes, calculators) to increase time on site",
            "Implement personalized product recommendations",
            "Create more video content - users engage 3x longer",
            "Add live chat support for real-time engagement",
        ],
        "performance": [
            "Optimize images - reduce page load time by ~40%",
            "Implement lazy loading for below-fold content",
            "Enable browser caching for static assets",
            "Minimize JavaScript bundle size",
        ],
        "general": [
            "Focus on mobile optimization - 60% of traffic is mobile",
            "Improve page load speed (current: 3.2s, target: <2s)",
            "Add email capture popup for cart abandonment recovery",
            "Implement retargeting campaigns for bounced users",
        ]
    }

    selected_recs = recommendations.get(focus_area, recommendations["general"])

    result = f"""
🎯 Optimization Recommendations - {focus_area.title()}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Priority Actions:

"""
    for i, rec in enumerate(selected_recs, 1):
        result += f"{i}. {rec}\n"

    result += f"\nExpected Impact: {random.choice(['High', 'Medium-High', 'Medium'])}"
    result += f"\nImplementation Difficulty: {random.choice(['Low', 'Medium', 'Low-Medium'])}"

    logger.info("Recommendations generated", extra={"focus_area": focus_area, "count": len(selected_recs)})
    return result


@tool
def calculate_roi(campaign_cost: float, revenue_generated: float) -> str:
    """
    Calculates ROI for marketing campaigns or initiatives.

    Args:
        campaign_cost: Total cost of the campaign/initiative
        revenue_generated: Revenue attributed to the campaign
    """
    logger.info(f"TOOL: Calculating ROI - Cost: ${campaign_cost}, Revenue: ${revenue_generated}")

    if campaign_cost == 0:
        return "Error: Campaign cost cannot be zero"

    roi_pct = ((revenue_generated - campaign_cost) / campaign_cost) * 100
    profit = revenue_generated - campaign_cost

    status = "Profitable" if roi_pct > 0 else "Loss"
    emoji = "📈" if roi_pct > 0 else "📉"

    result = f"""
{emoji} ROI Analysis:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Campaign Cost: ${campaign_cost:,.2f}
Revenue Generated: ${revenue_generated:,.2f}
Net Profit/Loss: ${profit:,.2f}

ROI: {roi_pct:+.2f}%
Status: {status}

Recommendation: {'Scale up investment' if roi_pct > 100 else 'Optimize campaign' if roi_pct > 0 else 'Pause and reassess strategy'}
"""

    logger.info("ROI calculated", extra={"roi_pct": roi_pct, "profit": profit, "status": status})
    return result


# --- Agent Class ---
class SentryAgent:
    def __init__(self, model):
        self.model = model

    def analyze_data(self, state: SentryState, config: dict):
        """
        The first step: The Sentry analyzes data and identifies insights.
        """
        logger.info("NODE: Analyzing Data")

        user_id = config["configurable"]["user_id"]

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are 'The Sentry', an expert analytics and business intelligence agent. "
                        "Your mission is to monitor metrics, detect anomalies, and provide actionable insights. "
                        "Use available tools to fetch performance data, analyze user behavior, and detect anomalies. "
                        "Provide clear, data-driven recommendations to improve business outcomes. "
                        "When analyzing, always: "
                        "1. Start by fetching current metrics using fetch_performance_metrics "
                        "2. Check for anomalies in key metrics using detect_anomalies "
                        "3. Analyze user behavior patterns if relevant "
                        "4. Generate specific, actionable recommendations "
                        "Return your final analysis as a JSON object with: "
                        '{"type": "analytics_report", "insights": "key findings", '
                        '"recommendations": "specific actions", "metrics": "relevant data"}. '
                        "Be concise but thorough. Focus on actionable insights, not just data."
                    ),
                ),
                ("human", "{request}"),
            ]
        )

        chain = prompt | self.model.bind_tools(
            [
                fetch_performance_metrics,
                detect_anomalies,
                analyze_user_behavior,
                generate_optimization_recommendations,
                calculate_roi,
            ]
        )

        user_request = state["messages"][-1].content
        response = chain.invoke({"request": user_request})

        return {"messages": [response]}

    def generate_insights(self, state: SentryState):
        """
        The second step: Execute tools and generate final insights report.
        """
        logger.info("NODE: Generating Insights")

        assistant_message = state["messages"][-1]

        # Execute tool calls
        tool_outputs = []
        for tool_call in assistant_message.tool_calls:
            try:
                tool_output = globals()[tool_call["name"]].invoke(tool_call["args"])
                tool_outputs.append(
                    ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
                )
                logger.info(
                    f"Tool '{tool_call['name']}' executed successfully",
                    extra={"tool_call_id": tool_call["id"]},
                )
            except Exception as e:
                error_message = f"Error executing tool '{tool_call['name']}': {e}"
                logger.error(
                    error_message,
                    extra={"tool_call_id": tool_call["id"], "error": str(e)},
                )
                tool_outputs.append(
                    ToolMessage(
                        content=f"Error: {error_message}", tool_call_id=tool_call["id"]
                    )
                )

        new_messages = state["messages"] + tool_outputs
        response = self.model.invoke(new_messages)

        return {"messages": [response]}


# --- Graph Definition ---
def get_sentry_agent():
    """
    Initializes and compiles The Sentry agent graph.
    """
    llm = ChatOpenAI(model="gpt-4-turbo")
    sentry_agent = SentryAgent(model=llm)

    workflow = StateGraph(SentryState)

    # Add nodes
    workflow.add_node("analyze", sentry_agent.analyze_data)
    workflow.add_node("insights", sentry_agent.generate_insights)

    # Define edges
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "insights")
    workflow.add_edge("insights", END)

    # Compile
    app = workflow.compile()

    return app


# --- Example Usage ---
if __name__ == "__main__":
    logger.info("This is a blueprint for The Sentry agent.")
    logger.info("To run it as a service, integrate with main.py and uvicorn server.")
