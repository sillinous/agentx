# Provider Integration Guide

This document describes how to configure and use external API providers for video generation, audio processing, and AI services.

## Overview

The Unified Media Asset Manager supports multiple external providers for content generation:

| Category | Provider | Features |
|----------|----------|----------|
| Video | Runway ML | Text-to-video, Image-to-video (Gen-3 Alpha) |
| Audio TTS | ElevenLabs | High-quality voice synthesis, 11+ voices |
| Audio Transcription | OpenAI Whisper | Speech-to-text transcription |
| AI | Anthropic Claude | Narrative generation, content analysis |

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Video Generation - Runway ML
RUNWAY_API_KEY=your-runway-api-key-here

# Audio TTS - ElevenLabs
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here

# Audio Transcription - OpenAI Whisper
OPENAI_API_KEY=your-openai-api-key-here

# AI Agent - Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Provider Mode (mock or real)
VIDEO_PROVIDER=mock
AUDIO_TTS_PROVIDER=mock
AUDIO_TRANSCRIBE_PROVIDER=mock
```

### Getting API Keys

1. **Runway ML**: https://runwayml.com/
   - Sign up and navigate to API settings
   - Copy your API key

2. **ElevenLabs**: https://elevenlabs.io/
   - Create account and go to Profile Settings
   - Copy your API key

3. **OpenAI**: https://platform.openai.com/
   - Create account and navigate to API keys
   - Generate a new secret key

4. **Anthropic**: https://console.anthropic.com/
   - Create account and navigate to API keys
   - Generate a new API key

---

## Provider Reference

### Runway ML (Video Generation)

**Supported Features:**
- Text-to-video generation
- Image-to-video generation
- Multiple aspect ratios (16:9, 9:16, 1:1)
- 5 or 10 second video duration

**Usage Example:**

```python
from app.providers.runway import RunwayProvider

provider = RunwayProvider()

# Generate video
result = await provider.generate_video(
    prompt="A futuristic city at sunset with flying cars",
    duration=5,
    aspect_ratio="16:9"
)

# Poll for completion
status = await provider.wait_for_completion(result["job_id"])
print(f"Video URL: {status['video_url']}")
```

**Pricing:**
- Gen-3 Alpha Turbo: ~$0.05 per second of video
- 5 second video: ~$0.25
- 10 second video: ~$0.50

---

### ElevenLabs (Text-to-Speech)

**Supported Features:**
- 11+ premium voices
- Multiple languages
- Voice customization (stability, similarity)
- MP3, WAV, OGG output formats

**Available Voices:**

| Alias | Voice | Description |
|-------|-------|-------------|
| default | Rachel | Neutral, American female |
| echo | Arnold | Male, authoritative |
| fable | Gigi | British female |
| onyx | Patrick | Deep male |
| nova | Bella | Female, warm |
| shimmer | Elli | Soft female |

**Usage Example:**

```python
from app.providers.elevenlabs import ElevenLabsProvider

provider = ElevenLabsProvider()

# Generate speech
result = await provider.text_to_speech(
    text="Welcome to our story universe.",
    voice="nova",
    stability=0.5,
    similarity_boost=0.75
)

# Save audio
with open("output.mp3", "wb") as f:
    f.write(result["audio_data"])
```

**Pricing:**
- Free tier: 10,000 characters/month
- Starter: $5/month for 30,000 characters
- Creator: $22/month for 100,000 characters

---

## Mock Providers

For development and testing, mock providers are available that simulate API responses without making actual API calls.

Set provider mode to `mock` in your `.env`:

```bash
VIDEO_PROVIDER=mock
AUDIO_TTS_PROVIDER=mock
```

Mock providers:
- Return sample/placeholder data
- Don't require API keys
- Have no rate limits
- Respond instantly

---

## Error Handling

All providers raise `ProviderError` exceptions with:
- `message`: Human-readable error description
- `provider`: Provider name (runway, elevenlabs, etc.)
- `details`: Additional error context

**Example:**

```python
from app.providers.base import ProviderError

try:
    result = await provider.generate_video(prompt="test")
except ProviderError as e:
    print(f"Error from {e.provider}: {e.message}")
    print(f"Details: {e.details}")
```

---

## Health Checks

Each provider includes a health check method:

```python
status = await provider.health_check()
if status["status"] == "ok":
    print("Provider is ready")
else:
    print(f"Provider error: {status['message']}")
```

---

## Best Practices

1. **Always use mock providers in development** to avoid costs
2. **Handle errors gracefully** - providers can fail due to rate limits, network issues, etc.
3. **Monitor usage** - especially for ElevenLabs character limits
4. **Use appropriate aspect ratios** for your content (16:9 for YouTube, 9:16 for TikTok)
5. **Cache results** when possible to reduce API calls

---

## Troubleshooting

### "API key not configured"
- Ensure the environment variable is set
- Check for typos in variable names
- Restart the server after changing `.env`

### "Insufficient credits" (Runway)
- Check your Runway account balance
- Add credits at https://runwayml.com/settings/billing

### "Rate limit exceeded"
- Wait and retry
- Consider upgrading your plan
- Implement request queuing

### "Invalid request"
- Check input parameters
- Ensure text isn't too long (ElevenLabs: 5000 chars max)
- Verify aspect ratio is supported
