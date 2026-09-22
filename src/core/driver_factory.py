"""Create Selenium WebDriver instances from ``config.settings``.

Only Chromium browsers (Chrome / Edge) are supported on purpose: the test
target is the Twitch WAP site, and ``mobileEmulation`` is Chromium-only.
"""

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from config.settings import Settings

_BROWSERS = {
    "chrome": (webdriver.ChromeOptions, webdriver.Chrome),
    "edge": (webdriver.EdgeOptions, webdriver.Edge),
}


def create_driver(settings: Settings | None = None) -> WebDriver:
    """Return a Chromium WebDriver emulating ``settings.device``."""
    settings = settings or Settings()
    browser = settings.browser.lower()
    try:
        options_cls, driver_cls = _BROWSERS[browser]
    except KeyError:
        raise ValueError(
            f"Unsupported browser: {browser!r}. "
            f"Mobile emulation requires one of: {sorted(_BROWSERS)}"
        ) from None

    options = options_cls()
    options.add_experimental_option("mobileEmulation", settings.device.as_cdp_payload())
    # Twitch autoplays live video, so the `load` event is unreliable;
    # page objects decide when a page is fully loaded.
    options.page_load_strategy = "eager"
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    # aria-label locators depend on UI language; `--lang` is ignored on macOS.
    options.add_experimental_option("prefs", {"intl.accept_languages": "en-US,en"})
    options.add_argument("--mute-audio")
    if settings.headless:
        options.add_argument("--headless=new")

    driver = driver_cls(options=options)
    driver.set_page_load_timeout(settings.page_load_timeout)
    return driver
