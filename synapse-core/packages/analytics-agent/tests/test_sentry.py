"""
Tests for The Sentry - Analytics and Monitoring Agent

These tests verify the tool functions work correctly without requiring
an actual OpenAI API key. The agent creation and invocation are tested
separately via the marketing-agent's integration tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, UTC

import sys
import os

# Set up test environment before imports
os.environ["TESTING"] = "1"
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock ChatOpenAI before importing sentry
with patch("langchain_openai.ChatOpenAI"):
    from sentry import (
        get_performance_metrics,
        detect_anomalies,
        analyze_traffic_trends,
        generate_insights_report,
        set_alert_threshold,
        SentryState,
    )


class TestGetPerformanceMetrics:
    """Tests for the get_performance_metrics tool."""

    def test_returns_metrics_structure(self):
        """Test that performance metrics returns expected structure."""
        result = get_performance_metrics.invoke({"user_id": "user-123", "time_range": "24h"})

        assert "time_range" in result
        assert result["time_range"] == "24h"
        assert "page_load_time" in result
        assert "api_response_time" in result
        assert "error_rate" in result
        assert "uptime" in result
        assert "requests_per_minute" in result

    def test_page_load_time_has_percentiles(self):
        """Test that page load metrics include percentile data."""
        result = get_performance_metrics.invoke({"user_id": "user-123"})

        page_load = result["page_load_time"]
        assert "avg_ms" in page_load
        assert "p50_ms" in page_load
        assert "p95_ms" in page_load
        assert "p99_ms" in page_load

    def test_api_response_time_has_percentiles(self):
        """Test that API response metrics include percentile data."""
        result = get_performance_metrics.invoke({"user_id": "user-123"})

        api_time = result["api_response_time"]
        assert "avg_ms" in api_time
        assert "p50_ms" in api_time
        assert "p95_ms" in api_time
        assert "p99_ms" in api_time

    def test_default_time_range(self):
        """Test that default time range is applied."""
        result = get_performance_metrics.invoke({"user_id": "user-123"})
        assert result["time_range"] == "24h"

    def test_custom_time_range(self):
        """Test that custom time range is used."""
        result = get_performance_metrics.invoke({"user_id": "user-123", "time_range": "7d"})
        assert result["time_range"] == "7d"


class TestDetectAnomalies:
    """Tests for the detect_anomalies tool."""

    def test_detects_slow_page_load(self):
        """Test that slow page load times are detected as anomalies."""
        metrics = {
            "page_load_time": {"p95_ms": 3500},  # Above 3000ms threshold
            "error_rate": 0.01,
        }

        result = detect_anomalies.invoke({"metrics": metrics})

        assert result["anomalies_detected"] >= 1
        anomaly_types = [a["type"] for a in result["anomalies"]]
        assert "slow_page_load" in anomaly_types

    def test_detects_high_error_rate(self):
        """Test that high error rates are detected as anomalies."""
        metrics = {
            "page_load_time": {"p95_ms": 1000},
            "error_rate": 0.10,  # 10% - above 5% threshold
        }

        result = detect_anomalies.invoke({"metrics": metrics})

        assert result["anomalies_detected"] >= 1
        anomaly_types = [a["type"] for a in result["anomalies"]]
        assert "high_error_rate" in anomaly_types

    def test_no_anomalies_when_healthy(self):
        """Test that healthy metrics don't trigger anomalies."""
        metrics = {
            "page_load_time": {"p95_ms": 1500},  # Below 3000ms
            "error_rate": 0.01,  # Below 5%
        }

        result = detect_anomalies.invoke({"metrics": metrics})

        assert result["anomalies_detected"] == 0
        assert result["anomalies"] == []
        assert result["health_score"] == 100

    def test_health_score_decreases_with_anomalies(self):
        """Test that health score decreases based on anomaly count."""
        metrics = {
            "page_load_time": {"p95_ms": 5000},
            "error_rate": 0.15,
        }

        result = detect_anomalies.invoke({"metrics": metrics})

        # With 2 anomalies, score should be 100 - (2 * 15) = 70
        assert result["health_score"] < 100
        assert result["health_score"] == 70

    def test_anomaly_has_required_fields(self):
        """Test that anomalies contain required fields."""
        metrics = {
            "page_load_time": {"p95_ms": 5000},
            "error_rate": 0.01,
        }

        result = detect_anomalies.invoke({"metrics": metrics})

        for anomaly in result["anomalies"]:
            assert "type" in anomaly
            assert "severity" in anomaly
            assert "message" in anomaly
            assert "recommendation" in anomaly


class TestAnalyzeTrafficTrends:
    """Tests for the analyze_traffic_trends tool."""

    def test_returns_traffic_structure(self):
        """Test that traffic trends returns expected structure."""
        result = analyze_traffic_trends.invoke({"user_id": "user-123", "days": 7})

        assert "period_days" in result
        assert "total_visitors" in result
        assert "unique_visitors" in result
        assert "page_views" in result
        assert "bounce_rate" in result
        assert "avg_session_duration_seconds" in result

    def test_includes_trend_data(self):
        """Test that trend data is included."""
        result = analyze_traffic_trends.invoke({"user_id": "user-123"})

        assert "trend" in result
        trend = result["trend"]
        assert "visitors_change" in trend
        assert "page_views_change" in trend
        assert "bounce_rate_change" in trend

    def test_includes_top_pages(self):
        """Test that top pages are included."""
        result = analyze_traffic_trends.invoke({"user_id": "user-123"})

        assert "top_pages" in result
        assert len(result["top_pages"]) > 0

        for page in result["top_pages"]:
            assert "path" in page
            assert "views" in page

    def test_includes_traffic_sources(self):
        """Test that traffic sources are included."""
        result = analyze_traffic_trends.invoke({"user_id": "user-123"})

        assert "traffic_sources" in result
        sources = result["traffic_sources"]
        assert "organic" in sources
        assert "direct" in sources
        assert "referral" in sources
        assert "social" in sources

    def test_default_days(self):
        """Test that default days value is applied."""
        result = analyze_traffic_trends.invoke({"user_id": "user-123"})
        assert result["period_days"] == 7


class TestGenerateInsightsReport:
    """Tests for the generate_insights_report tool."""

    def test_returns_insights_structure(self):
        """Test that insights report returns expected structure."""
        metrics = {"page_load_time": {"avg_ms": 1500}}
        trends = {"trend": {"visitors_change": 0.05}, "bounce_rate": 0.3}

        result = generate_insights_report.invoke({"metrics": metrics, "trends": trends})

        assert "generated_at" in result
        assert "insights_count" in result
        assert "insights" in result
        assert "summary" in result

    def test_detects_slow_page_load_insight(self):
        """Test that slow page loads generate performance insight."""
        metrics = {"page_load_time": {"avg_ms": 2500}}  # Above 2000ms
        trends = {"trend": {"visitors_change": 0.05}, "bounce_rate": 0.3}

        result = generate_insights_report.invoke({"metrics": metrics, "trends": trends})

        categories = [i["category"] for i in result["insights"]]
        assert "performance" in categories

    def test_detects_growth_insight(self):
        """Test that traffic growth generates growth insight."""
        metrics = {"page_load_time": {"avg_ms": 1000}}
        trends = {"trend": {"visitors_change": 0.15}, "bounce_rate": 0.3}  # 15% growth

        result = generate_insights_report.invoke({"metrics": metrics, "trends": trends})

        categories = [i["category"] for i in result["insights"]]
        assert "growth" in categories

    def test_detects_high_bounce_rate_insight(self):
        """Test that high bounce rate generates engagement insight."""
        metrics = {"page_load_time": {"avg_ms": 1000}}
        trends = {"trend": {"visitors_change": 0.05}, "bounce_rate": 0.65}  # Above 50%

        result = generate_insights_report.invoke({"metrics": metrics, "trends": trends})

        categories = [i["category"] for i in result["insights"]]
        assert "engagement" in categories

    def test_insight_has_required_fields(self):
        """Test that insights contain required fields."""
        metrics = {"page_load_time": {"avg_ms": 2500}}
        trends = {"trend": {"visitors_change": 0.15}, "bounce_rate": 0.65}

        result = generate_insights_report.invoke({"metrics": metrics, "trends": trends})

        for insight in result["insights"]:
            assert "category" in insight
            assert "insight" in insight
            assert "impact" in insight
            assert "action" in insight

    def test_generated_at_is_iso_format(self):
        """Test that generated_at is in ISO format."""
        metrics = {"page_load_time": {"avg_ms": 1000}}
        trends = {"trend": {"visitors_change": 0.05}, "bounce_rate": 0.3}

        result = generate_insights_report.invoke({"metrics": metrics, "trends": trends})

        # Should parse without error
        datetime.fromisoformat(result["generated_at"].replace("Z", "+00:00"))


class TestSetAlertThreshold:
    """Tests for the set_alert_threshold tool."""

    def test_returns_configuration(self):
        """Test that alert threshold returns configuration."""
        result = set_alert_threshold.invoke({
            "metric_name": "error_rate",
            "threshold": 0.05,
            "comparison": "gt",
        })

        assert result["status"] == "configured"
        assert "alert" in result
        assert "message" in result

    def test_alert_config_structure(self):
        """Test that alert configuration has required fields."""
        result = set_alert_threshold.invoke({
            "metric_name": "page_load_time",
            "threshold": 3000,
        })

        alert = result["alert"]
        assert alert["metric"] == "page_load_time"
        assert alert["threshold"] == 3000
        assert "comparison" in alert
        assert "notification_channels" in alert

    def test_default_comparison(self):
        """Test that default comparison is 'gt'."""
        result = set_alert_threshold.invoke({
            "metric_name": "error_rate",
            "threshold": 0.05,
        })

        assert result["alert"]["comparison"] == "gt"

    def test_custom_comparison(self):
        """Test that custom comparison is used."""
        result = set_alert_threshold.invoke({
            "metric_name": "uptime",
            "threshold": 99.9,
            "comparison": "lt",
        })

        assert result["alert"]["comparison"] == "lt"

    def test_notification_channels_included(self):
        """Test that notification channels are included."""
        result = set_alert_threshold.invoke({
            "metric_name": "error_rate",
            "threshold": 0.05,
        })

        channels = result["alert"]["notification_channels"]
        assert "email" in channels
        assert "slack" in channels


class TestSentryState:
    """Tests for the SentryState TypedDict."""

    def test_state_has_required_keys(self):
        """Test that SentryState has all required keys."""
        state: SentryState = {
            "messages": [],
            "metrics_type": "all",
            "time_range": "24h",
            "user_id": "user-123",
            "thread_id": "thread-456",
        }

        assert "messages" in state
        assert "metrics_type" in state
        assert "time_range" in state
        assert "user_id" in state
        assert "thread_id" in state
