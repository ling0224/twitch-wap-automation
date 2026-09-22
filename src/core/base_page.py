"""Base class for page objects.

Owns the generic definition of "loaded" and the element primitives every page
needs. Site knowledge (locators, pop-ups) stays out of core: pop-up handling is
injected through the ``PopupDismisser`` protocol, which
``src.components.popup_handler.PopupHandler`` satisfies.
"""

from __future__ import annotations

import logging
from typing import Protocol, Self, TypeVar
from urllib.parse import urljoin, urlparse

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC

from config.settings import Settings
from src.core.retry import retry_on_transient
from src.core.waits import Condition, document_complete, layout_settled, viewport_width, wait_for

log = logging.getLogger(__name__)

Locator = tuple[str, str]
T = TypeVar("T")
P = TypeVar("P", bound="BasePage")


class PopupDismisser(Protocol):
    def dismiss_all(self) -> list[str]: ...


class BasePage:
    #: Path relative to ``settings.base_url``; set on pages that can be opened directly.
    path: str | None = None
    #: Element whose visibility means this specific page has rendered.
    ready_locator: Locator | None = None

    def __init__(self, driver: WebDriver, settings: Settings, popups: PopupDismisser | None = None) -> None:
        self.driver = driver
        self.settings = settings
        self.popups = popups

    # --- navigation -------------------------------------------------------

    def open(self) -> Self:
        if self.path is None:
            raise TypeError(f"{type(self).__name__} has no path; reach it by navigating from another page")
        self.driver.get(urljoin(self.settings.base_url, self.path))
        return self.wait_until_loaded()

    def go_to(self, page_cls: type[P]) -> P:
        """Hand the session to the next page object once that page has loaded."""
        return page_cls(self.driver, self.settings, self.popups).wait_until_loaded()

    def wait_until_loaded(self) -> Self:
        """Document complete -> layout settled -> pop-ups dismissed -> page-specific element visible.

        Order matters: pop-ups rendered during hydration intercept clicks.
        Subclasses extend this (call ``super()``) for stricter definitions.
        """
        self.wait(document_complete, "document.readyState never reached 'complete'")
        self.wait(layout_settled, "page kept overflowing the viewport horizontally")
        if self.popups is not None:
            self.popups.dismiss_all()
        if self.ready_locator is not None:
            print(f"waiting for ready_locator {self.ready_locator} to be visible")
            self.visible(self.ready_locator)
        return self

    # --- element primitives -----------------------------------------------

    def wait(self, condition: Condition[T], message: str = "") -> T:
        return wait_for(self.driver, condition, self.settings.default_timeout, message)

    def find(self, locator: Locator) -> WebElement:
        return self.wait(EC.presence_of_element_located(locator), f"not present: {locator}")

    def visible(self, locator: Locator) -> WebElement:
        return self.wait(EC.visibility_of_element_located(locator), f"not visible: {locator}")

    def find_all(self, locator: Locator) -> list[WebElement]:
        return self.driver.find_elements(*locator)

    @retry_on_transient()
    def wait_and_click(self, locator: Locator) -> None:
        element = self.wait(EC.element_to_be_clickable(locator), f"not clickable: {locator}")
        self.scroll_into_view(element)
        element.click()

    @retry_on_transient()
    def click_element(self, element: WebElement) -> None:
        """Click an element already in hand, e.g. one card out of ``find_all``."""
        self.scroll_into_view(element)
        element.click()

    def js_click(self, locator: Locator) -> None:
        """Dispatch a click to the element itself, bypassing whatever covers its centre.

        Only for full-size layers whose centre is always covered by another
        control (e.g. a player's tap layer under the pause button); anything
        with its own visible control should use ``wait_and_click``.
        """
        self.driver.execute_script("arguments[0].click();", self.find(locator))

    @retry_on_transient()
    def type_text(self, locator: Locator, text: str, clear: bool = True) -> None:
        element = self.visible(locator)
        if clear:
            element.clear()
        element.send_keys(text)

    # --- scrolling --------------------------------------------------------

    def scroll_into_view(self, element: WebElement) -> None:
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', behavior: 'instant'});", element
        )

    def scroll_by_viewport(self, factor: float = 1.0) -> None:
        """One 'scroll down' == one viewport height, matching a user swipe."""
        self.driver.execute_script("window.scrollBy(0, window.innerHeight * arguments[0]);", factor)

    def scroll_position(self) -> int:
        return int(self.driver.execute_script("return window.scrollY;"))

    def viewport_height(self) -> int:
        return int(self.driver.execute_script("return window.innerHeight;"))

    def scroll_one_viewport(self) -> None:
        """Scroll exactly one viewport down, waiting out infinite lists.

        Hitting the bottom is what triggers an infinite list to load its next
        page, so the scroll is re-issued on every poll until the target is
        reached; the browser clamps each attempt to the current page height.
        """
        target = self.scroll_position() + self.viewport_height()
        log.info("Scrolling one viewport down to y=%s", target)

        def reached(_) -> bool:
            self.driver.execute_script("window.scrollTo(0, arguments[0]);", target)
            return self.scroll_position() >= target

        self.wait(reached, f"could not scroll to y={target}; end of the page?")

    # --- guards -----------------------------------------------------------

    def assert_wap_layout(self) -> None:
        """Fail fast if we got the desktop site instead of the emulated mobile one."""
        log.info("Asserting WAP layout for %s at %s", self.settings.device_name, self.driver.current_url)
        expected_host = urlparse(self.settings.base_url).netloc
        actual_host = urlparse(self.driver.current_url).netloc
        assert actual_host == expected_host, f"expected host {expected_host}, got {actual_host}"
        width = viewport_width(self.driver)
        assert width == self.settings.device.width, (
            f"viewport {width}px != {self.settings.device_name} width {self.settings.device.width}px"
        )
