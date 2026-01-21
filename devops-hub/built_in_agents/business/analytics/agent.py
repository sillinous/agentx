"""Analytics Agent - Process and analyze data metrics."""

import logging
from datetime import datetime
from typing import Any, Dict, List

from built_in_agents.base import (
    AgentCapability, AgentContext, AgentMessage, AgentResponse, BaseAgent, Protocol,
)

logger = logging.getLogger(__name__)


class AnalyticsAgent(BaseAgent):
    """Agent for data analysis and metrics processing."""

    def __init__(self):
        super().__init__(
            agent_id="analytics-agent",
            name="Analytics Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.ANP, Protocol.MCP],
        )

    def _register_default_capabilities(self) -> None:
        self.register_capability(AgentCapability(
            name="calculate_stats",
            description="Calculate statistics for a dataset",
            parameters={"data": {"type": "array", "description": "Numeric array"}},
            returns={
                "count": {"type": "integer"},
                "sum": {"type": "number"},
                "mean": {"type": "number"},
                "min": {"type": "number"},
                "max": {"type": "number"},
            },
        ))

        self.register_capability(AgentCapability(
            name="aggregate",
            description="Aggregate data by a field",
            parameters={
                "data": {"type": "array"},
                "group_by": {"type": "string"},
                "metric": {"type": "string"},
            },
            returns={"aggregations": {"type": "object"}},
        ))

        self.register_capability(AgentCapability(
            name="trend_analysis",
            description="Analyze trends in time-series data",
            parameters={
                "data": {"type": "array"},
                "time_field": {"type": "string"},
                "value_field": {"type": "string"},
            },
            returns={"trend": {"type": "string"}, "change_percent": {"type": "number"}},
        ))

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        capability = message.capability
        payload = message.payload

        if capability == "calculate_stats":
            data = payload.get("data", [])
            if not data or not all(isinstance(x, (int, float)) for x in data):
                return AgentResponse.error_response("Data must be a numeric array")
            result = {
                "count": len(data),
                "sum": sum(data),
                "mean": sum(data) / len(data) if data else 0,
                "min": min(data) if data else 0,
                "max": max(data) if data else 0,
            }
            return AgentResponse.success_response(result)

        elif capability == "aggregate":
            data = payload.get("data", [])
            group_by = payload.get("group_by", "")
            result = self._aggregate(data, group_by)
            return AgentResponse.success_response({"aggregations": result})

        elif capability == "trend_analysis":
            data = payload.get("data", [])
            value_field = payload.get("value_field", "value")
            result = self._analyze_trend(data, value_field)
            return AgentResponse.success_response(result)

        return AgentResponse.error_response(f"Unknown capability: {capability}")

    def _aggregate(self, data: List[Dict], group_by: str) -> Dict:
        """Aggregate data by field."""
        groups: Dict[str, List] = {}
        for item in data:
            key = str(item.get(group_by, "unknown"))
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return {k: {"count": len(v)} for k, v in groups.items()}

    def _analyze_trend(self, data: List[Dict], value_field: str) -> Dict:
        """Simple trend analysis."""
        if not data or len(data) < 2:
            return {"trend": "insufficient_data", "change_percent": 0}
        values = [item.get(value_field, 0) for item in data]
        first, last = values[0], values[-1]
        if first == 0:
            return {"trend": "unknown", "change_percent": 0}
        change = ((last - first) / first) * 100
        trend = "increasing" if change > 0 else "decreasing" if change < 0 else "stable"
        return {"trend": trend, "change_percent": round(change, 2)}
