from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver

from config.settings import Settings
from src.components.popup_handler import PopupHandler
from src.core.base_page import BasePage, PopupDismisser


class TwitchPage(BasePage):
    """Base for every m.twitch.tv page object: pop-up handling is on by default.

    Callers never have to know which page shows which pop-up; pass ``popups``
    only to substitute a different dismisser (e.g. a fake in tests).
    ``go_to`` hands the same instance to the next page.
    """

    def __init__(self, driver: WebDriver, settings: Settings, popups: PopupDismisser | None = None) -> None:
        super().__init__(driver, settings, popups or PopupHandler(driver, settings.default_timeout))
