import json
import urllib.error
import urllib.request
from typing import Any, Dict

from .base import BaseProvider, ServiceUnavailableError


class ClaudeProvider(BaseProvider):
    def __init__(self, model: str, api_key: str = "", base_url: str = ""):
        super().__init__(model=model, api_key=api_key, base_url=base_url)

    def query(self, system_prompt: str, user_prompt: str, timeout: int = 180) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("No Claude API key provided. Run 'should-i-update --configure' or set ANTHROPIC_API_KEY.")

        url = "https://api.anthropic.com/v1/messages"

        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "User-Agent": "Should-i-Update/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                contents = result.get("content", [])
                text = "".join(part.get("text", "") for part in contents if part.get("type") == "text")
                return self.extract_json(text)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            if e.code == 503:
                raise ServiceUnavailableError(f"Claude API 503 Service Unavailable: {error_body}")
            raise RuntimeError(f"Claude API error ({e.code}): {error_body}")
        except Exception as e:
            raise RuntimeError(f"Failed to query Claude API: {e}")

