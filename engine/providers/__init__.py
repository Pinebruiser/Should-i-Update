from typing import Any, Dict

from .base import BaseProvider
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from .openai import OpenAIProvider


def get_provider(provider_name: str, config: Dict[str, Any], api_key: str = "") -> BaseProvider:
    name = (provider_name or config.get("provider", "gemini")).lower()
    model = config.get("curr_model", "")

    if name == "gemini":
        return GeminiProvider(model=model, api_key=api_key)
    elif name == "groq":
        return GroqProvider(model=model, api_key=api_key)
    elif name == "claude":
        return ClaudeProvider(model=model, api_key=api_key)
    elif name == "openai":
        return OpenAIProvider(model=model, api_key=api_key)
    else:
        raise ValueError(f"Unknown provider '{name}'. Supported: gemini, groq, claude, openai.")
