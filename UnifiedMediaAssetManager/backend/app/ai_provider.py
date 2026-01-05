import os
import time
import random
from typing import Dict, Optional
import requests

# Pluggable AI provider interface for image generation.
# Implementations should return a dict with at least {'url': '<image_url>'}

AI_PROVIDER = os.environ.get("AI_PROVIDER", "placeholder")
RETRY_ATTEMPTS = int(os.environ.get("AI_RETRY_ATTEMPTS", "3"))


def _placeholder_generate(prompt: str) -> Dict[str, str]:
    """Use via.placeholder.com to create a simple image URL containing the prompt."""
    from urllib.parse import quote
    encoded = quote(prompt)
    return {"url": f"https://via.placeholder.com/1024x1024.png?text={encoded}", "provider": "placeholder"}


def generate_image(prompt: str, timeout: int = 30) -> Dict[str, str]:
    """Generate an image using the configured provider with simple retry/backoff.

    Returns a dict with keys: url, provider
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            if AI_PROVIDER == "placeholder":
                return _placeholder_generate(prompt)

            # Example for future provider hooks (HTTP): PROVIDER_HTTP
            if AI_PROVIDER == "http":
                provider_url = os.environ.get("AI_PROVIDER_HTTP_URL")
                if not provider_url:
                    raise RuntimeError("AI_PROVIDER_HTTP_URL not set")
                resp = requests.post(provider_url, json={"prompt": prompt}, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                # Expecting {'url': '...'} from provider
                return {"url": data.get("url"), "provider": "http"}

            # Unknown provider: fall back to placeholder
            return _placeholder_generate(prompt)

        except Exception as e:
            last_exc = e
            wait = min(2 ** attempt + random.random(), 10)
            time.sleep(wait)
            continue

    # If we exhausted retries, raise the last exception
    if last_exc:
        raise last_exc
    return {"url": "", "provider": AI_PROVIDER}
