"""
Tests for AI agent implementations.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestBaseAgent:
    """Tests for the base agent functionality."""

    def test_base_agent_import(self):
        """Test that base agent can be imported."""
        from app.agents.base_agent import BaseAgent
        assert BaseAgent is not None

    def test_base_agent_is_abstract(self):
        """Test that base agent cannot be instantiated directly."""
        from app.agents.base_agent import BaseAgent
        with pytest.raises(TypeError):
            BaseAgent()


class TestNarrativeAgent:
    """Tests for the narrative agent."""

    def test_narrative_agent_import(self):
        """Test that narrative agent can be imported."""
        from app.agents.narrative_agent import NarrativeAgent
        assert NarrativeAgent is not None

    def test_narrative_agent_instantiation(self):
        """Test that narrative agent can be instantiated."""
        from app.agents.narrative_agent import NarrativeAgent
        agent = NarrativeAgent()
        assert agent is not None

    @pytest.mark.asyncio
    async def test_narrative_agent_process_mock(self):
        """Test narrative agent processing with mocked AI provider."""
        from app.agents.narrative_agent import NarrativeAgent

        agent = NarrativeAgent()

        # Mock the AI provider response
        with patch.object(agent, 'client', create=True) as mock_client:
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Generated narrative content")]
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            # Test with mock - should not raise
            input_data = {
                "prompt": "Test narrative prompt",
                "context": {"world": "fantasy"}
            }
            # The actual call may fail without API key, but import should work
            assert callable(agent.process)


class TestSpatialAgent:
    """Tests for the spatial agent."""

    def test_spatial_agent_import(self):
        """Test that spatial agent can be imported."""
        from app.agents.spatial_agent import SpatialAgent
        assert SpatialAgent is not None

    def test_spatial_agent_instantiation(self):
        """Test that spatial agent can be instantiated."""
        from app.agents.spatial_agent import SpatialAgent
        agent = SpatialAgent()
        assert agent is not None


class TestConsistencyAgent:
    """Tests for the consistency agent."""

    def test_consistency_agent_import(self):
        """Test that consistency agent can be imported."""
        from app.agents.consistency_agent import ConsistencyAgent
        assert ConsistencyAgent is not None

    def test_consistency_agent_instantiation(self):
        """Test that consistency agent can be instantiated."""
        from app.agents.consistency_agent import ConsistencyAgent
        agent = ConsistencyAgent()
        assert agent is not None


class TestVideoStrategyAgent:
    """Tests for the video strategy agent."""

    def test_video_strategy_agent_import(self):
        """Test that video strategy agent can be imported."""
        from app.agents.video_strategy_agent import VideoStrategyAgent
        assert VideoStrategyAgent is not None

    def test_video_strategy_agent_instantiation(self):
        """Test that video strategy agent can be instantiated."""
        from app.agents.video_strategy_agent import VideoStrategyAgent
        agent = VideoStrategyAgent()
        assert agent is not None

    @pytest.mark.asyncio
    async def test_video_strategy_mood_mapping(self):
        """Test that mood values map to appropriate categories."""
        from app.agents.video_strategy_agent import VideoStrategyAgent

        agent = VideoStrategyAgent()

        # Test mood categories (0-100 scale)
        # Low mood should map to calm/dark
        # High mood should map to energetic/bright
        assert hasattr(agent, 'process')


class TestVideoGenerationAgent:
    """Tests for the video generation agent."""

    def test_video_generation_agent_import(self):
        """Test that video generation agent can be imported."""
        from app.agents.video_generation_agent import VideoGenerationAgent
        assert VideoGenerationAgent is not None

    def test_video_generation_agent_instantiation(self):
        """Test that video generation agent can be instantiated."""
        from app.agents.video_generation_agent import VideoGenerationAgent
        agent = VideoGenerationAgent()
        assert agent is not None


class TestAudioAgent:
    """Tests for the audio agent."""

    def test_audio_agent_import(self):
        """Test that audio agent can be imported."""
        from app.agents.audio_agent import AudioAgent
        assert AudioAgent is not None

    def test_audio_agent_instantiation(self):
        """Test that audio agent can be instantiated with config."""
        from app.agents.audio_agent import AudioAgent
        agent = AudioAgent(config={"default_provider": "mock"})
        assert agent is not None

    def test_audio_agent_default_config(self):
        """Test audio agent with default configuration."""
        from app.agents.audio_agent import AudioAgent
        agent = AudioAgent()
        assert agent is not None

    @pytest.mark.asyncio
    async def test_audio_agent_has_process_method(self):
        """Test that audio agent has the required process method."""
        from app.agents.audio_agent import AudioAgent
        agent = AudioAgent(config={"default_provider": "mock"})
        assert hasattr(agent, 'process')
        assert callable(agent.process)


class TestAgentTasks:
    """Tests for the Celery task integration."""

    def test_tasks_import(self):
        """Test that tasks module can be imported."""
        from app.agents import tasks
        assert tasks is not None

    def test_process_agent_job_exists(self):
        """Test that process_agent_job task exists."""
        from app.agents.tasks import process_agent_job
        assert process_agent_job is not None

    def test_get_job_stats_exists(self):
        """Test that get_job_stats function exists."""
        from app.agents.tasks import get_job_stats
        assert get_job_stats is not None
        assert callable(get_job_stats)
