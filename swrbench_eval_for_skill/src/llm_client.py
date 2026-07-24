"""Minimal OpenAI-compatible LLM client."""
import os
import time
import random
from typing import Any, Dict, List, Optional

# Optional dependency: if openai is not installed, evaluation can still be run
# with user-supplied review files.
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from loguru import logger


def run_chat(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.0,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict[str, Any]] = None,
    api_base: Optional[str] = None,
    api_key: Optional[str] = None,
    max_retries: int = 3,
) -> Optional[str]:
    """Call an OpenAI-compatible chat completion endpoint.

    Args:
        model: Model name.
        messages: OpenAI messages format.
        temperature: Sampling temperature.
        max_tokens: Max output tokens.
        response_format: Optional JSON schema response format dict.
        api_base: Override API base URL.
        api_key: Override API key.
        max_retries: Number of retries on failure.

    Returns:
        Raw model output string, or None if all retries failed.
    """
    if not HAS_OPENAI:
        raise RuntimeError(
            "The 'openai' package is required for LLM judging. "
            "Install it with: pip install openai"
        )

    base_url = (api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")).rstrip("/")
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please set it in the environment or pass api_key."
        )

    client = OpenAI(base_url=base_url, api_key=key)
    last_error = None
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            if response_format is not None:
                kwargs["response_format"] = response_format

            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            last_error = e
            logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(2 ** attempt + random.random())
        finally:
            client.close()

    logger.error(f"LLM call failed after {max_retries} attempts: {last_error}")
    return None
