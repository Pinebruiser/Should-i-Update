import os
import shutil
import subprocess
from typing import Optional

ENV_MAP = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


def get_api_key(provider: str) -> Optional[str]:
    """Retrieve the API key for a given provider.
    Priority:
    1. SHOULD_I_UPDATE_API_KEY env var
    2. Provider-specific env var (e.g., GEMINI_API_KEY)
    3. Linux Secret Service via secret-tool
    """
    prov = provider.lower()

    # 1 & 2: Environment variables
    if os.environ.get("SHOULD_I_UPDATE_API_KEY"):
        return os.environ["SHOULD_I_UPDATE_API_KEY"].strip()

    env_var = ENV_MAP.get(prov)
    if env_var and os.environ.get(env_var):
        return os.environ[env_var].strip()

    # 3: secret-tool (Linux Secret Service)
    secret_tool = shutil.which("secret-tool")
    if secret_tool:
        try:
            res = subprocess.run(
                [secret_tool, "lookup", "service", "should-i-update", "provider", prov],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    return None


def store_api_key(provider: str, api_key: str) -> bool:
    """Store the API key securely into the Linux Secret Service."""
    prov = provider.lower()
    secret_tool = shutil.which("secret-tool")

    if secret_tool:
        try:
            p = subprocess.run(
                [
                    secret_tool,
                    "store",
                    f"--label=Should-i-Update API Key ({prov})",
                    "service",
                    "should-i-update",
                    "provider",
                    prov,
                ],
                input=api_key.strip(),
                text=True,
                capture_output=True,
                timeout=5,
            )
            if p.returncode == 0:
                return True
        except Exception:
            pass

    return False


def clear_api_key(provider: str) -> bool:
    """Remove the API key from the Linux Secret Service."""
    prov = provider.lower()
    secret_tool = shutil.which("secret-tool")

    if secret_tool:
        try:
            subprocess.run(
                [secret_tool, "clear", "service", "should-i-update", "provider", prov],
                capture_output=True,
                timeout=5,
            )
            return True
        except Exception:
            pass

    return False

