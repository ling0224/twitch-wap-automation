"""Named, timestamped screenshots of the current viewport.

Deciding *when* the page is worth capturing is the page object's job
(e.g. ``StreamerPage.wait_until_loaded``); this module only writes the file.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver

log = logging.getLogger(__name__)


def capture(driver: WebDriver, name: str, directory: Path) -> Path:
    """Save the viewport as ``<directory>/<YYYYmmdd-HHMMSS>_<name>.png`` and return the path.

    The timestamp keeps earlier runs from being overwritten; ``name`` is
    reduced to filename-safe characters.
    """
    directory.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^\w.-]+", "_", name).strip("_") or "screenshot"
    path = directory / f"{datetime.now():%Y%m%d-%H%M%S}_{slug}.png"
    if not driver.save_screenshot(str(path)):
        raise OSError(f"WebDriver could not write screenshot to {path}")
    log.info("Screenshot saved: %s", path)
    return path
