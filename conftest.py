"""Test lifecycle: CLI options -> Settings, one driver per test, failure screenshots.

Page behaviour (pop-ups, "loaded") lives in the page objects, not here; this
file only wires things together so tests can just ask for ``home``.
"""

from __future__ import annotations

import base64
import re
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

try:
    import pytest_html
except ImportError:  # report plugin is optional; screenshots are still saved to disk
    pytest_html = None

from config.devices import DEFAULT_DEVICE
from config.settings import Settings
from src.core.driver_factory import create_driver
from src.core.screenshot import capture
from src.pages.home_page import HomePage


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("twitch", "Twitch WAP run configuration (overrides env vars)")
    group.addoption("--device", help=f"device profile name from config/devices.py (env: DEVICE), default = {DEFAULT_DEVICE}")
    group.addoption("--headless", action="store_true", default=None, help="run without a window (env: HEADLESS)")


@pytest.fixture(scope="session")
def settings(pytestconfig: pytest.Config) -> Settings:
    """Precedence: CLI flag > env var > default (env and defaults are resolved by Settings)."""
    cli = {
        "device_name": pytestconfig.getoption("--device"),
        "headless": pytestconfig.getoption("--headless"),
    }
    settings = replace(Settings(), **{k: v for k, v in cli.items() if v is not None})
    settings.device  # fail once, at session start, on an unknown device name
    return settings


@pytest.fixture
def driver(settings: Settings) -> Iterator[WebDriver]:
    driver = create_driver(settings)
    yield driver
    driver.quit()


@pytest.fixture
def home(driver: WebDriver, settings: Settings) -> HomePage:
    """Twitch home page, opened, WAP layout confirmed and pop-ups dismissed."""
    page = HomePage(driver, settings).open()
    page.assert_wap_layout()
    return page


@pytest.fixture
def screenshot(driver: WebDriver, settings: Settings, request: pytest.FixtureRequest):
    """Returns a callable so tests can capture named screenshots on demand.

    Each capture is saved under ``settings.screenshots_dir`` and embedded in the HTML report.
    """
    extras = request.getfixturevalue("extras") if pytest_html is not None else None

    def _capture(name: str) -> Path:
        path = capture(driver, name, settings.screenshots_dir)
        if extras is not None:
            extras.append(pytest_html.extras.png(base64.b64encode(path.read_bytes()).decode(), name=name))
        return path

    return _capture


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """Screenshot the browser when a test body fails; save it and embed it in the HTML report."""
    report = yield
    funcargs = getattr(item, "funcargs", {})
    driver = funcargs.get("driver")
    if report.when == "call" and report.failed and driver is not None:
        png = driver.get_screenshot_as_png()
        failures_dir = funcargs["settings"].screenshots_dir / "failures"  # driver depends on settings
        failures_dir.mkdir(parents=True, exist_ok=True)
        (failures_dir / f"{re.sub(r'[^\w.-]+', '_', item.nodeid)}.png").write_bytes(png)
        if pytest_html is not None:  # embedded as base64 so --self-contained-html keeps it
            report.extras = [*getattr(report, "extras", []), pytest_html.extras.png(base64.b64encode(png).decode())]
    return report
