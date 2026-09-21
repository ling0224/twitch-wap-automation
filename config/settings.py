"""Single source of truth for run configuration.

Precedence: pytest CLI flag > environment variable > default.
Tests never read env vars directly; they receive a `Settings` instance.
"""

from __future__ import annotations

import os
from pathlib import Path
from dataclasses import dataclass, field

from config.devices import DEFAULT_DEVICE, DeviceProfile, get_device_profile

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(key: str, default: bool = False) -> bool:
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes", "on"}

def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except ValueError:
        return default


@dataclass
class Settings:
    """Configuration settings for the test run."""
    debug: bool = False
    environment: str = "staging"
    log_level: str = "INFO"

    base_url: str = field(default_factory=lambda: os.getenv("BASE_URL", "https://m.twitch.tv/"))
    browser: str = field(default_factory=lambda: os.getenv("BROWSER", "chrome"))
    device_name: str = field(default_factory=lambda: os.getenv("DEVICE", DEFAULT_DEVICE))
    headless: bool = field(default_factory=lambda: _env_bool("HEADLESS", False))

    # Timeouts (seconds)
    default_timeout: int = field(default_factory=lambda: _env_int("TIMEOUT", 30))
    page_load_timeout: int = field(default_factory=lambda: _env_int("PAGE_LOAD_TIMEOUT", 30))

    @property
    def device(self) -> DeviceProfile:
        """Return the DeviceProfile for the specified device name."""
        return get_device_profile(self.device_name)
