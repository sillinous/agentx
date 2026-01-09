# Monitor Agent
# Monitors agent health, metrics, and performance across ecosystem

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from collections import deque
import asyncio
import logging
import statistics

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
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """Metrics for a monitored agent."""
    agent_id: str
    status: str = "unknown"
    last_check: Optional[datetime] = None
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    error_count: int = 0
    request_count: int = 0
    uptime_start: Optional[datetime] = None
    custom_metrics: Dict[str, deque] = field(default_factory=dict)


@dataclass
class Alert:
    """An alert raised by monitoring."""
    id: str
    agent_id: str
    severity: str
    message: str
    metric: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False


class MonitorAgent(BaseAgent):
    """
    Monitor Agent - Comprehensive monitoring for the agent ecosystem.

    Capabilities:
    - health-monitoring: Monitor agent health status
    - metrics-collection: Collect and aggregate metrics
    - performance-tracking: Track performance over time
    - alerting: Generate and manage alerts
    - observability: Provide system-wide observability
    """

    def __init__(self):
        super().__init__(
            agent_id="monitor-agent",
            name="Monitor Agent",
            version="1.0.0",
            protocols=[Protocol.A2A, Protocol.ACP, Protocol.ANP],
        )

        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._alerts: List[Alert] = []
        self._alert_rules: Dict[str, Dict[str, Any]] = {}
        self._metric_buffer: Dict[str, deque] = {}
        self._alert_handlers: List[Callable] = []
        self._check_interval: int = 30

    def _register_default_capabilities(self) -> None:
        """Register monitor capabilities."""
        self.register_capability(AgentCapability(
            name="health-monitoring",
            description="Monitor and report agent health status",
            parameters={
                "agent_ids": {"type": "array", "description": "Agents to monitor"},
                "action": {"type": "string", "enum": ["check", "status", "history"]},
            },
            returns={"type": "object", "properties": {"status": "object", "agents": "array"}},
        ))

        self.register_capability(AgentCapability(
            name="metrics-collection",
            description="Collect and query metrics",
            parameters={
                "action": {"type": "string", "enum": ["record", "query", "aggregate"]},
                "metric": {"type": "string", "description": "Metric name"},
                "value": {"type": "number", "description": "Metric value"},
            },
            returns={"type": "object"},
        ))

        self.register_capability(AgentCapability(
            name="performance-tracking",
            description="Track and analyze performance",
            parameters={
                "agent_id": {"type": "string", "description": "Agent to track"},
                "window": {"type": "string", "enum": ["1m", "5m", "15m", "1h", "1d"]},
            },
            returns={"type": "object", "properties": {"metrics": "object"}},
        ))

        self.register_capability(AgentCapability(
            name="alerting",
            description="Manage alerts and notifications",
            parameters={
                "action": {"type": "string", "enum": ["list", "acknowledge", "configure"]},
                "alert_id": {"type": "string", "description": "Alert ID"},
            },
            returns={"type": "object"},
        ))

        self.register_capability(AgentCapability(
            name="observability",
            description="System-wide observability dashboard",
            parameters={
                "view": {"type": "string", "enum": ["summary", "detailed", "topology"]},
            },
            returns={"type": "object"},
        ))

        # Register handlers
        self.register_handler("health-monitoring", self._handle_health)
        self.register_handler("metrics-collection", self._handle_metrics)
        self.register_handler("performance-tracking", self._handle_performance)
        self.register_handler("alerting", self._handle_alerting)
        self.register_handler("observability", self._handle_observability)

    async def process_message(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Process incoming messages."""
        if message.capability in self._message_handlers:
            return await self._message_handlers[message.capability](message, context)

        return AgentResponse.error_response(
            f"Unknown capability: {message.capability}",
            error_code="UNKNOWN_CAPABILITY",
        )

    async def _handle_health(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle health monitoring requests."""
        payload = message.payload
        action = payload.get("action", "status")
        agent_ids = payload.get("agent_ids", list(self._agent_metrics.keys()))

        if action == "status":
            statuses = []
            for agent_id in agent_ids:
                if agent_id in self._agent_metrics:
                    metrics = self._agent_metrics[agent_id]
                    statuses.append({
                        "agent_id": agent_id,
                        "status": metrics.status,
                        "last_check": metrics.last_check.isoformat() if metrics.last_check else None,
                        "error_count": metrics.error_count,
                        "request_count": metrics.request_count,
                        "uptime_seconds": (
                            (datetime.utcnow() - metrics.uptime_start).total_seconds()
                            if metrics.uptime_start else 0
                        ),
                    })

            healthy = sum(1 for s in statuses if s["status"] == "healthy")
            return AgentResponse.success_response({
                "agents": statuses,
                "summary": {
                    "total": len(statuses),
                    "healthy": healthy,
                    "unhealthy": len(statuses) - healthy,
                    "health_percentage": (healthy / len(statuses) * 100) if statuses else 100,
                },
            })

        elif action == "check":
            # Perform health checks
            results = []
            for agent_id in agent_ids:
                result = await self._check_agent_health(agent_id)
                results.append(result)

            return AgentResponse.success_response({
                "checks": results,
                "timestamp": datetime.utcnow().isoformat(),
            })

        elif action == "history":
            agent_id = payload.get("agent_id")
            if agent_id and agent_id in self._agent_metrics:
                metrics = self._agent_metrics[agent_id]
                return AgentResponse.success_response({
                    "agent_id": agent_id,
                    "response_times": list(metrics.response_times),
                    "error_count": metrics.error_count,
                    "request_count": metrics.request_count,
                })

        return AgentResponse.error_response(
            f"Unknown action: {action}",
            error_code="UNKNOWN_ACTION",
        )

    async def _handle_metrics(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle metrics collection."""
        payload = message.payload
        action = payload.get("action", "query")

        if action == "record":
            metric_name = payload.get("metric")
            value = payload.get("value")
            agent_id = payload.get("agent_id", "system")
            tags = payload.get("tags", {})

            if not metric_name:
                return AgentResponse.error_response(
                    "metric name is required",
                    error_code="MISSING_PARAMETER",
                )

            self._record_metric(metric_name, value, agent_id, tags)

            return AgentResponse.success_response({
                "recorded": True,
                "metric": metric_name,
                "value": value,
            })

        elif action == "query":
            metric_name = payload.get("metric")
            agent_id = payload.get("agent_id")
            window = payload.get("window", "5m")

            if metric_name:
                data = self._query_metric(metric_name, agent_id, window)
                return AgentResponse.success_response({
                    "metric": metric_name,
                    "data": data,
                })
            else:
                # List all metrics
                metrics = list(self._metric_buffer.keys())
                return AgentResponse.success_response({
                    "metrics": metrics,
                    "total": len(metrics),
                })

        elif action == "aggregate":
            metric_name = payload.get("metric")
            agg_type = payload.get("aggregation", "avg")
            window = payload.get("window", "5m")

            if not metric_name:
                return AgentResponse.error_response(
                    "metric name is required",
                    error_code="MISSING_PARAMETER",
                )

            result = self._aggregate_metric(metric_name, agg_type, window)
            return AgentResponse.success_response({
                "metric": metric_name,
                "aggregation": agg_type,
                "value": result,
                "window": window,
            })

        return AgentResponse.error_response(
            f"Unknown action: {action}",
            error_code="UNKNOWN_ACTION",
        )

    async def _handle_performance(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle performance tracking."""
        payload = message.payload
        agent_id = payload.get("agent_id")
        window = payload.get("window", "5m")

        if agent_id and agent_id in self._agent_metrics:
            metrics = self._agent_metrics[agent_id]

            response_times = list(metrics.response_times)
            if response_times:
                perf = {
                    "avg_response_time_ms": statistics.mean(response_times),
                    "min_response_time_ms": min(response_times),
                    "max_response_time_ms": max(response_times),
                    "p50_response_time_ms": statistics.median(response_times),
                    "p95_response_time_ms": (
                        sorted(response_times)[int(len(response_times) * 0.95)]
                        if len(response_times) >= 20 else max(response_times)
                    ),
                    "request_count": metrics.request_count,
                    "error_rate": (
                        metrics.error_count / metrics.request_count
                        if metrics.request_count > 0 else 0
                    ),
                }
            else:
                perf = {
                    "avg_response_time_ms": 0,
                    "request_count": 0,
                    "error_rate": 0,
                }

            return AgentResponse.success_response({
                "agent_id": agent_id,
                "window": window,
                "performance": perf,
            })

        # System-wide performance
        total_requests = sum(m.request_count for m in self._agent_metrics.values())
        total_errors = sum(m.error_count for m in self._agent_metrics.values())

        return AgentResponse.success_response({
            "system": {
                "total_agents": len(self._agent_metrics),
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": total_errors / total_requests if total_requests > 0 else 0,
            },
        })

    async def _handle_alerting(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle alerting operations."""
        payload = message.payload
        action = payload.get("action", "list")

        if action == "list":
            severity = payload.get("severity")
            acknowledged = payload.get("acknowledged")

            alerts = self._alerts
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            if acknowledged is not None:
                alerts = [a for a in alerts if a.acknowledged == acknowledged]

            return AgentResponse.success_response({
                "alerts": [
                    {
                        "id": a.id,
                        "agent_id": a.agent_id,
                        "severity": a.severity,
                        "message": a.message,
                        "metric": a.metric,
                        "value": a.value,
                        "threshold": a.threshold,
                        "timestamp": a.timestamp.isoformat(),
                        "acknowledged": a.acknowledged,
                    }
                    for a in alerts
                ],
                "total": len(alerts),
            })

        elif action == "acknowledge":
            alert_id = payload.get("alert_id")
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    return AgentResponse.success_response({
                        "acknowledged": True,
                        "alert_id": alert_id,
                    })
            return AgentResponse.error_response(
                f"Alert not found: {alert_id}",
                error_code="ALERT_NOT_FOUND",
            )

        elif action == "configure":
            rule_name = payload.get("rule_name")
            rule = payload.get("rule", {})
            self._alert_rules[rule_name] = rule
            return AgentResponse.success_response({
                "configured": True,
                "rule_name": rule_name,
            })

        return AgentResponse.error_response(
            f"Unknown action: {action}",
            error_code="UNKNOWN_ACTION",
        )

    async def _handle_observability(self, message: AgentMessage, context: AgentContext) -> AgentResponse:
        """Handle observability requests."""
        payload = message.payload
        view = payload.get("view", "summary")

        if view == "summary":
            total_agents = len(self._agent_metrics)
            healthy = sum(1 for m in self._agent_metrics.values() if m.status == "healthy")
            total_alerts = len([a for a in self._alerts if not a.acknowledged])

            return AgentResponse.success_response({
                "agents": {
                    "total": total_agents,
                    "healthy": healthy,
                    "unhealthy": total_agents - healthy,
                },
                "alerts": {
                    "total": len(self._alerts),
                    "unacknowledged": total_alerts,
                    "critical": len([a for a in self._alerts if a.severity == "critical" and not a.acknowledged]),
                },
                "metrics": {
                    "total_metrics": len(self._metric_buffer),
                },
                "timestamp": datetime.utcnow().isoformat(),
            })

        elif view == "detailed":
            agents_detail = []
            for agent_id, metrics in self._agent_metrics.items():
                agents_detail.append({
                    "agent_id": agent_id,
                    "status": metrics.status,
                    "request_count": metrics.request_count,
                    "error_count": metrics.error_count,
                    "avg_response_time": (
                        statistics.mean(metrics.response_times)
                        if metrics.response_times else 0
                    ),
                })

            return AgentResponse.success_response({
                "agents": agents_detail,
                "alerts": [
                    {
                        "id": a.id,
                        "severity": a.severity,
                        "message": a.message,
                    }
                    for a in self._alerts[:10]  # Last 10 alerts
                ],
            })

        return AgentResponse.error_response(
            f"Unknown view: {view}",
            error_code="UNKNOWN_VIEW",
        )

    async def _check_agent_health(self, agent_id: str) -> Dict[str, Any]:
        """Perform a health check on an agent."""
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)

        metrics = self._agent_metrics[agent_id]
        metrics.last_check = datetime.utcnow()

        # Simulate health check (in real impl, would ping agent)
        metrics.status = "healthy"

        return {
            "agent_id": agent_id,
            "status": metrics.status,
            "checked_at": metrics.last_check.isoformat(),
        }

    def _record_metric(
        self,
        name: str,
        value: float,
        agent_id: str,
        tags: Dict[str, str],
    ) -> None:
        """Record a metric value."""
        key = f"{agent_id}:{name}"
        if key not in self._metric_buffer:
            self._metric_buffer[key] = deque(maxlen=1000)

        self._metric_buffer[key].append(MetricPoint(
            timestamp=datetime.utcnow(),
            value=value,
            tags=tags,
        ))

    def _query_metric(
        self,
        name: str,
        agent_id: Optional[str],
        window: str,
    ) -> List[Dict[str, Any]]:
        """Query metric values."""
        window_seconds = self._parse_window(window)
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)

        results = []
        for key, points in self._metric_buffer.items():
            if agent_id and not key.startswith(f"{agent_id}:"):
                continue
            if name not in key:
                continue

            for point in points:
                if point.timestamp >= cutoff:
                    results.append({
                        "timestamp": point.timestamp.isoformat(),
                        "value": point.value,
                        "tags": point.tags,
                    })

        return results

    def _aggregate_metric(
        self,
        name: str,
        agg_type: str,
        window: str,
    ) -> float:
        """Aggregate metric values."""
        window_seconds = self._parse_window(window)
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)

        values = []
        for key, points in self._metric_buffer.items():
            if name not in key:
                continue
            for point in points:
                if point.timestamp >= cutoff:
                    values.append(point.value)

        if not values:
            return 0.0

        if agg_type == "avg":
            return statistics.mean(values)
        elif agg_type == "sum":
            return sum(values)
        elif agg_type == "min":
            return min(values)
        elif agg_type == "max":
            return max(values)
        elif agg_type == "count":
            return len(values)
        else:
            return statistics.mean(values)

    def _parse_window(self, window: str) -> int:
        """Parse window string to seconds."""
        if window.endswith("m"):
            return int(window[:-1]) * 60
        elif window.endswith("h"):
            return int(window[:-1]) * 3600
        elif window.endswith("d"):
            return int(window[:-1]) * 86400
        return 300  # Default 5 minutes

    # Public API

    def register_agent_for_monitoring(self, agent_id: str) -> None:
        """Register an agent for monitoring."""
        self._agent_metrics[agent_id] = AgentMetrics(
            agent_id=agent_id,
            status="healthy",
            uptime_start=datetime.utcnow(),
        )

    def record_request(self, agent_id: str, response_time_ms: float, error: bool = False) -> None:
        """Record a request for an agent."""
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = AgentMetrics(agent_id=agent_id)

        metrics = self._agent_metrics[agent_id]
        metrics.request_count += 1
        metrics.response_times.append(response_time_ms)
        if error:
            metrics.error_count += 1

    def raise_alert(
        self,
        agent_id: str,
        severity: str,
        message: str,
        metric: str,
        value: float,
        threshold: float,
    ) -> Alert:
        """Raise a new alert."""
        from uuid import uuid4
        alert = Alert(
            id=str(uuid4()),
            agent_id=agent_id,
            severity=severity,
            message=message,
            metric=metric,
            value=value,
            threshold=threshold,
        )
        self._alerts.append(alert)

        # Notify handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

        return alert

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        total = len(self._agent_metrics)
        healthy = sum(1 for m in self._agent_metrics.values() if m.status == "healthy")

        return {
            "status": "healthy" if healthy == total else "degraded",
            "agents_healthy": healthy,
            "agents_total": total,
            "active_alerts": len([a for a in self._alerts if not a.acknowledged]),
        }
