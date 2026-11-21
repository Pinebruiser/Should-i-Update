import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_MODELS: Dict[str, str] = {
    "gemini": "gemini-3-6-flash",
    "openrouter": "openrouter/auto",
    "claude": "claude-3-5-haiku-20241022",
    "openai": "gpt-4o-mini",
}

DEFAULT_CONFIG: Dict[str, Any] = {
    "provider": "gemini",
    "curr_model": "",
    "saved_models": {},
    "request_timeout": 180,
    "check_aur": True,
    "aur_helper": "yay",
    "update_command": "sudo pacman -Syu",
    "check_arch_news": True,
}


def get_default_model(provider: str) -> str:
    """Return the default model for a given provider."""
    return DEFAULT_MODELS.get(provider.lower(), "")


def get_config_dir() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "should-i-update"
    return Path.home() / ".config" / "should-i-update"


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def load_config() -> Dict[str, Any]:
    config_file = get_config_path()
    config = DEFAULT_CONFIG.copy()
    needs_save = False

    if config_file.is_file():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                config.update(user_config)
        except Exception:
            pass


    if "saved_models" not in config or not isinstance(config["saved_models"], dict):
        config["saved_models"] = {}
        needs_save = True

    current_prov = config.get("provider", "gemini").lower()
    current_model = config.get("curr_model", "")

    if current_model:
        if config["saved_models"].get(current_prov) != current_model:
            config["saved_models"][current_prov] = current_model
            needs_save = True
    else:
        resolved_model = config["saved_models"].get(current_prov) or get_default_model(current_prov)
        config["curr_model"] = resolved_model
        config["saved_models"][current_prov] = resolved_model
        needs_save = True

    if needs_save and config_file.is_file():
        try:
            save_config(config)
        except Exception:
            pass

    return config


def set_provider(provider: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Switch active provider and restore/preserve custom models per provider."""
    config = load_config()
    old_prov = config.get("provider", "gemini").lower()
    current_model = config.get("curr_model", "")

    if "saved_models" not in config or not isinstance(config["saved_models"], dict):
        config["saved_models"] = {}

    if current_model:
        config["saved_models"][old_prov] = current_model

    new_prov = provider.lower()
    config["provider"] = new_prov

    if model:
        config["curr_model"] = model
        config["saved_models"][new_prov] = model
    else:
        saved_model = config["saved_models"].get(new_prov)
        config["curr_model"] = saved_model or get_default_model(new_prov)
        if new_prov not in config["saved_models"]:
            config["saved_models"][new_prov] = config["curr_model"]

    save_config(config)
    return config


def save_config(config: Dict[str, Any]) -> None:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = get_config_path()

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
