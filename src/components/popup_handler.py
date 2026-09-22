"""Recursive dismissal of known pop-ups / modals.

``dismiss_all`` closes the first visible known pop-up, then solves the same
problem again on the new DOM, because closing one pop-up can reveal another.

Base cases:
    * no known pop-up visible and no unknown modal  -> done
    * an unknown modal is visible                   -> fail (add it to KNOWN_POPUPS)
    * depth reaches ``max_depth``                   -> fail (pop-ups keep re-opening)

Call it after the page has settled (``waits.layout_settled``): pop-ups that
render during hydration report wrong coordinates and intercept clicks.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from src.core.retry import retry_on_transient
from src.core.waits import wait_for

log = logging.getLogger(__name__)

Locator = tuple[str, str]


@dataclass(frozen=True)
class Popup:
    """A dismissable interstitial.

    `container` detects it, `dismiss` is the control that closes it. They are
    often the same element, but not always (an overlay detected by its
    container, closed by a nested button).
    """

    name: str
    container: Locator
    dismiss: Locator


KNOWN_POPUPS: tuple[Popup, ...] = (
    Popup(
        name="open_in_app_sheet",
        container=(By.CSS_SELECTOR, '[role="dialog"][aria-label="Open in App or Login Options"]'),
        # No data-a-target on this button; text is stable because the locale is pinned to en-US.
        dismiss=(By.XPATH, '//*[@role="dialog"]//button[.//p[normalize-space()="Keep using web"]]'),
    ),
)

_VISIBLE_MODAL_LABELS = """
return [...document.querySelectorAll('[aria-modal="true"]')]
  .filter(el => el.getClientRects().length > 0)
  .map(el => el.getAttribute('aria-label') || el.outerHTML.slice(0, 120));
"""


class PopupError(AssertionError):
    """A pop-up could not be dismissed; the page is not in a testable state."""


class PopupHandler:
    def __init__(
        self,
        driver: WebDriver,
        timeout: float,
        popups: tuple[Popup, ...] = KNOWN_POPUPS,
        max_depth: int = 5,
    ) -> None:
        self.driver = driver
        self.timeout = timeout
        self.popups = popups
        self.max_depth = max_depth

    def dismiss_all(self, depth: int = 0) -> list[str]:
        """Dismiss every visible known pop-up; return their names in dismissal order."""
        popup = self._first_visible()
        if popup is None:
            self._fail_on_unknown_modal()
            return []
        if depth >= self.max_depth:
            raise PopupError(f"Pop-ups still open after {self.max_depth} dismissals (last: {popup.name})")

        log.info("Dismissing pop-up %r (depth %s)", popup.name, depth)
        self._dismiss(popup)
        return [popup.name, *self.dismiss_all(depth + 1)]

    def _first_visible(self) -> Popup | None:
        return next((p for p in self.popups if self._visible(p.container) is not None), None)

    def _visible(self, locator: Locator) -> WebElement | None:
        for element in self.driver.find_elements(*locator):
            try:
                if element.is_displayed():
                    return element
            except StaleElementReferenceException:
                continue  # re-rendered between find and check; treat as gone
        return None

    @retry_on_transient()
    def _dismiss(self, popup: Popup) -> None:
        button = wait_for(
            self.driver,
            lambda _: self._visible(popup.dismiss),
            self.timeout,
            f"{popup.name}: dismiss button not visible",
        )
        button.click()
        wait_for(
            self.driver,
            lambda _: self._visible(popup.container) is None,
            self.timeout,
            f"{popup.name}: still visible after clicking dismiss",
        )

    def _fail_on_unknown_modal(self) -> None:
        labels = self.driver.execute_script(_VISIBLE_MODAL_LABELS)
        if labels:
            raise PopupError(f"Unknown modal(s) visible, add to KNOWN_POPUPS: {labels}")
