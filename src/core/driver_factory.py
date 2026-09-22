"""Create Selenium WebDriver instances from ``config.settings``.

Chrome only, on purpose: the test target is the Twitch WAP site, which needs
ChromeDriver's ``mobileEmulation`` (device metrics + client hints).
"""

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from config.settings import Settings


def create_driver(settings: Settings | None = None) -> WebDriver:
    """Return a Chrome WebDriver emulating ``settings.device``."""
    settings = settings or Settings()

    options = webdriver.ChromeOptions()
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

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(settings.page_load_timeout)
    return driver
