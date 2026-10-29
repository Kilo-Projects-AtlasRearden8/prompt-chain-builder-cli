"""Configuration loading for prompt-chain-builder-cli."""

import json
import os

DEFAULT_ENDPOINT = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3"
DEFAULT_TIMEOUT = 60

CONFIG_FILE_NAMES = ("prompt-chain.json", ".prompt-chain.json")


def load_config(path=None):
    """Load configuration from a JSON file, falling back to defaults.

    Returns a dict with keys: endpoint, model, timeout.
    """
    config = {
        "endpoint": DEFAULT_ENDPOINT,
        "model": DEFAULT_MODEL,
        "timeout": DEFAULT_TIMEOUT,
    }

    search_paths = []
    if path:
        search_paths.append(path)
    search_paths.extend(CONFIG_FILE_NAMES)

    for candidate in search_paths:
        if candidate and os.path.isfile(candidate):
            try:
                with open(candidate, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                if "endpoint" in data:
                    config["endpoint"] = data["endpoint"]
                if "model" in data:
                    config["model"] = data["model"]
                if "timeout" in data:
                    config["timeout"] = data["timeout"]
            break

    return config


def write_default_config(path="prompt-chain.json"):
    """Write a default configuration file if one does not already exist."""
    if os.path.exists(path):
        return False
    config = {
        "endpoint": DEFAULT_ENDPOINT,
        "model": DEFAULT_MODEL,
        "timeout": DEFAULT_TIMEOUT,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    return True
