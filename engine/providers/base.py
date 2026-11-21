import json
import re
from typing import Any, Dict


class ServiceUnavailableError(RuntimeError):
    """Raised when an upstream LLM provider returns HTTP 503 (service overloaded or unavailable)."""
    pass


class BaseProvider:
    def __init__(self, model: str, api_key: str = "", base_url: str = ""):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def query(self, system_prompt: str, user_prompt: str, timeout: int = 180) -> Dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def extract_json(raw_text: str) -> Dict[str, Any]:
        """Extract and parse JSON from raw LLM response text."""
        text = raw_text.strip()

        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass

        # Strip markdown ```json ... ``` codeblocks
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except Exception:
                pass

        # Find first '{' and last '}'
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            snippet = text[first_brace : last_brace + 1]
            try:
                return json.loads(snippet)
            except Exception:
                pass

        # Return a structured fallback
        return {
            "verdict": "UPGRADE_RECOMMENDED",
            "summary": raw_text[:300].strip(),
            "categories": {
                "UPNOW": [],
                "COOLFEAT": [],
                "IFYOUWANT": [],
                "REDUNDANT": [],
            },
        }

