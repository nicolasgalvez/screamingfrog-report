"""Load sfreport configuration from TOML files."""

import tomllib
from pathlib import Path

# Project-level overrides user-level
_CONFIG_PATHS = [
    Path.home() / ".sfreport.toml",
    Path(".sfreport.toml"),
]


def load_config() -> dict:
    """Load and merge config from ~/.sfreport.toml and ./.sfreport.toml.

    Project-level values override user-level values.
    """
    merged: dict = {}
    for path in _CONFIG_PATHS:
        if path.is_file():
            with open(path, "rb") as f:
                merged |= tomllib.load(f)
    return merged


def get_sf_binary() -> str:
    """Return the configured SF binary path, or the platform default."""
    from sfreport.crawl import SF_BINARY

    cfg = load_config()
    return cfg.get("screaming_frog", {}).get("binary", SF_BINARY)
