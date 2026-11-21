import json
import urllib.error
import urllib.request
from typing import Any, Dict

from .base import BaseProvider, ServiceUnavailableError


class OpenAIProvider(BaseProvider):
    def __init__(self, model: str, api_key: str = "", base_url: str = ""):
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
        )

    def query(self, system_prompt: str, user_prompt: str, timeout: int = 180) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("No OpenAI API key provided. Run 'should-i-update --configure' or set OPENAI_API_KEY.")

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
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
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Should-i-Update/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = (
                    result.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                return self.extract_json(text)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            if e.code == 503:
                raise ServiceUnavailableError(f"OpenAI API 503 Service Unavailable: {error_body}")
            raise RuntimeError(f"OpenAI API error ({e.code}): {error_body}")
        except Exception as e:
            raise RuntimeError(f"Failed to query OpenAI ({self.model}): {e}")
