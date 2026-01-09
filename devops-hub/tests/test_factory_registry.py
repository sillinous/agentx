"""
Unit tests for agent factory and registry.
"""

import pytest
import tempfile
from pathlib import Path

from factory.agent_registry import (
    AgentRegistry,
    AgentMetadata,
    AgentStatus,
    AgentDomain,
    AgentType,
    PerformanceMetrics,
)
from factory.agent_factory import AgentFactory


class TestAgentMetadata:
    """Tests for AgentMetadata."""

    def test_metadata_creation(self):
        metadata = AgentMetadata(
            id="test-agent",
            name="Test Agent",
            version="1.0.0",
            status=AgentStatus.PRODUCTION,
            domain=AgentDomain.UTILITY,
            agent_type=AgentType.WORKER,
            description="A test agent",
            capabilities=["cap1", "cap2"],
            protocols=["a2a/1.0"],
        )
        assert metadata.id == "test-agent"
        assert metadata.status == AgentStatus.PRODUCTION

    def test_metadata_to_dict(self):
        metadata = AgentMetadata(
            id="test-agent",
            name="Test Agent",
            version="1.0.0",
            status=AgentStatus.PRODUCTION,
            domain=AgentDomain.UTILITY,
            agent_type=AgentType.WORKER,
            description="Test",
            capabilities=["cap1"],
            protocols=["a2a/1.0"],
        )
        d = metadata.to_dict()
        assert d["id"] == "test-agent"
        assert d["status"] == "production"
        assert d["domain"] == "utility"

    def test_metadata_from_dict(self):
        data = {
            "id": "test-agent",
            "name": "Test Agent",
            "version": "1.0.0",
            "status": "production",
            "domain": "business",
            "type": "analyst",
            "description": "Test description",
            "capabilities": ["analysis", "reporting"],
            "protocols": ["a2a/1.0", "acp/1.0"],
        }
        metadata = AgentMetadata.from_dict(data)
        assert metadata.id == "test-agent"
        assert metadata.domain == AgentDomain.BUSINESS
        assert metadata.agent_type == AgentType.ANALYST

    def test_metadata_from_dict_defaults(self):
        data = {"id": "minimal", "name": "Minimal Agent"}
        metadata = AgentMetadata.from_dict(data)
        assert metadata.version == "1.0.0"
        assert metadata.status == AgentStatus.PRODUCTION
        assert metadata.domain == AgentDomain.UTILITY


class TestPerformanceMetrics:
    """Tests for PerformanceMetrics."""

    def test_default_metrics(self):
        metrics = PerformanceMetrics()
        assert metrics.max_concurrent_requests == 100
        assert metrics.uptime_percent == 99.9

    def test_custom_metrics(self):
        metrics = PerformanceMetrics(
            max_concurrent_requests=500,
            average_latency_ms=200,
            uptime_percent=99.99,
        )
        assert metrics.max_concurrent_requests == 500


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    @pytest.fixture
    def registry(self):
        return AgentRegistry()

    @pytest.fixture
    def sample_metadata(self):
        return AgentMetadata(
            id="test-agent",
            name="Test Agent",
            version="1.0.0",
            status=AgentStatus.PRODUCTION,
            domain=AgentDomain.BUSINESS,
            agent_type=AgentType.ANALYST,
            description="A test agent",
            capabilities=["analysis", "reporting"],
            protocols=["a2a/1.0"],
        )

    def test_register_agent(self, registry, sample_metadata):
        agent_id = registry.register(sample_metadata)
        assert agent_id == "test-agent"
        assert registry.count() == 1

    def test_register_duplicate_raises(self, registry, sample_metadata):
        registry.register(sample_metadata)
        with pytest.raises(ValueError):
            registry.register(sample_metadata)

    def test_get_agent(self, registry, sample_metadata):
        registry.register(sample_metadata)
        agent = registry.get("test-agent")
        assert agent is not None
        assert agent.name == "Test Agent"

    def test_get_nonexistent_agent(self, registry):
        assert registry.get("nonexistent") is None

    def test_list_all(self, registry, sample_metadata):
        registry.register(sample_metadata)

        another = AgentMetadata(
            id="another-agent",
            name="Another Agent",
            version="1.0.0",
            status=AgentStatus.PRODUCTION,
            domain=AgentDomain.UTILITY,
            agent_type=AgentType.WORKER,
            description="Another",
            capabilities=["other-cap"],
            protocols=["a2a/1.0"],
        )
        registry.register(another)

        all_agents = registry.list_all()
        assert len(all_agents) == 2

    def test_discover_by_domain(self, registry, sample_metadata):
        registry.register(sample_metadata)
        results = registry.discover(domain="business")
        assert len(results) == 1
        assert results[0].id == "test-agent"

    def test_discover_by_capability(self, registry, sample_metadata):
        registry.register(sample_metadata)
        results = registry.discover(capability="analysis")
        assert len(results) == 1

        results = registry.discover(capability="nonexistent")
        assert len(results) == 0

    def test_discover_by_status(self, registry, sample_metadata):
        registry.register(sample_metadata)
        results = registry.discover(status="production")
        assert len(results) == 1

    def test_discover_combined_filters(self, registry, sample_metadata):
        registry.register(sample_metadata)
        results = registry.discover(domain="business", status="production")
        assert len(results) == 1

        results = registry.discover(domain="system", status="production")
        assert len(results) == 0

    def test_update_agent(self, registry, sample_metadata):
        registry.register(sample_metadata)
        sample_metadata.description = "Updated description"
        registry.update(sample_metadata)
        updated = registry.get("test-agent")
        assert updated.description == "Updated description"

    def test_update_nonexistent_raises(self, registry, sample_metadata):
        with pytest.raises(KeyError):
            registry.update(sample_metadata)

    def test_get_capabilities(self, registry, sample_metadata):
        registry.register(sample_metadata)
        caps = registry.get_capabilities()
        assert "analysis" in caps
        assert "reporting" in caps

    def test_get_domains(self, registry, sample_metadata):
        registry.register(sample_metadata)
        domains = registry.get_domains()
        assert "business" in domains

    def test_registry_with_file_persistence(self, sample_metadata):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"agents": []}')
            temp_path = Path(f.name)

        try:
            registry = AgentRegistry(registry_path=temp_path)
            registry.register(sample_metadata)

            # Create new registry from same file
            new_registry = AgentRegistry(registry_path=temp_path)
            assert new_registry.count() == 1
            assert new_registry.get("test-agent") is not None
        finally:
            temp_path.unlink()


class TestAgentFactory:
    """Tests for AgentFactory."""

    @pytest.fixture
    def factory(self):
        return AgentFactory(strict_validation=False)

    @pytest.fixture
    def factory_sample_metadata(self):
        return AgentMetadata(
            id="factory-test-agent",
            name="Factory Test Agent",
            version="1.0.0",
            status=AgentStatus.DRAFT,
            domain=AgentDomain.UTILITY,
            agent_type=AgentType.WORKER,
            description="An agent for factory testing",
            capabilities=["test-cap"],
            protocols=["a2a/1.0"],
        )

    def test_register_agent(self, factory, factory_sample_metadata):
        agent_id = factory.register_agent(factory_sample_metadata, skip_validation=True)
        assert agent_id == "factory-test-agent"

    def test_get_agent(self, factory, factory_sample_metadata):
        factory.register_agent(factory_sample_metadata, skip_validation=True)
        agent = factory.get_agent("factory-test-agent")
        assert agent is not None
        assert agent.name == "Factory Test Agent"

    def test_discover_agents(self, factory, factory_sample_metadata):
        factory.register_agent(factory_sample_metadata, skip_validation=True)
        results = factory.discover_agents(domain="utility", status="draft")
        assert len(results) == 1

    def test_promote_to_production(self, factory, factory_sample_metadata):
        factory.register_agent(factory_sample_metadata, skip_validation=True)
        factory.promote_to_production("factory-test-agent")
        agent = factory.get_agent("factory-test-agent")
        assert agent.status == AgentStatus.PRODUCTION

    def test_deprecate_agent(self, factory, factory_sample_metadata):
        factory.register_agent(factory_sample_metadata, skip_validation=True)
        factory.deprecate_agent("factory-test-agent")
        agent = factory.get_agent("factory-test-agent")
        assert agent.status == AgentStatus.DEPRECATED

    def test_get_statistics(self, factory, factory_sample_metadata):
        factory.register_agent(factory_sample_metadata, skip_validation=True)
        stats = factory.get_statistics()
        assert stats["total_agents"] == 1
        assert "by_status" in stats
        assert "by_domain" in stats

    def test_validate_agent(self, factory, factory_sample_metadata):
        factory.register_agent(factory_sample_metadata, skip_validation=True)
        result = factory.validate_agent(agent_id="factory-test-agent")
        assert result is not None

    def test_pre_register_hook(self, factory, factory_sample_metadata):
        hook_called = []

        def hook(metadata):
            hook_called.append(metadata.id)

        factory._pre_register_hooks.append(hook)
        factory.register_agent(factory_sample_metadata, skip_validation=True)
        assert "factory-test-agent" in hook_called

    def test_post_register_hook(self, factory, factory_sample_metadata):
        hook_called = []

        def hook(metadata):
            hook_called.append(metadata.id)

        factory._post_register_hooks.append(hook)
        factory.register_agent(factory_sample_metadata, skip_validation=True)
        assert "factory-test-agent" in hook_called
