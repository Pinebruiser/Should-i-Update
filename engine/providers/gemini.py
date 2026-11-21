import json
import urllib.error
import urllib.request
from typing import Any, Dict

from .base import BaseProvider, ServiceUnavailableError


class GeminiProvider(BaseProvider):
    def __init__(self, model: str, api_key: str = "", base_url: str = ""):
        super().__init__(model=model, api_key=api_key, base_url=base_url)

    def query(self, system_prompt: str, user_prompt: str, timeout: int = 180) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("No Gemini API key provided. Run 'should-i-update --configure' or set GEMINI_API_KEY.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Should-i-Update/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text = (
                    result.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                return self.extract_json(text)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            if e.code == 503:
                raise ServiceUnavailableError(f"Gemini API 503 Service Unavailable: {error_body}")
            raise RuntimeError(f"Gemini API error ({e.code}): {error_body}")
        except Exception as e:
            raise RuntimeError(f"Failed to query Gemini API: {e}")
