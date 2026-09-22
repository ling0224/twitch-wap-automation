"""Explicit waits and reusable page conditions.

Conditions follow Selenium's expected_conditions style: a callable that takes
the driver and returns a truthy value once satisfied; page objects combine these into their own "fully loaded" definition.
There is no `time.sleep()` anywhere in the codebase.
"""

from __future__ import annotations

from typing import Callable, TypeVar

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

T = TypeVar("T")
Condition = Callable[[WebDriver], T]

POLL_FREQUENCY = 0.25


def wait_for(driver: WebDriver, condition: Condition[T], timeout: float, message: str = "") -> T:
    """Block until ``condition`` is truthy and return its value; raise TimeoutException otherwise."""
    return WebDriverWait(driver, timeout, poll_frequency=POLL_FREQUENCY).until(condition, message)


def document_complete(driver: WebDriver) -> bool:
    """``document.readyState == 'complete'`` (needed because page_load_strategy is eager)."""
    return driver.execute_script("return document.readyState") == "complete"


def layout_settled(driver: WebDriver) -> bool:
    """No horizontal overflow, i.e. the page has finished laying out for the viewport.

    During hydration m.twitch.tv briefly renders a container wider than the
    viewport (scrollWidth 1317 on a 393px device), which also inflates
    ``window.innerWidth``. ``clientWidth`` stays at the viewport width throughout.
    """
    return driver.execute_script(
        "const de = document.documentElement; return de.scrollWidth <= de.clientWidth"
    )


def viewport_width(driver: WebDriver) -> int:
    """Layout viewport width in CSS px; unlike ``innerWidth`` it ignores content overflow."""
    return driver.execute_script("return document.documentElement.clientWidth")

def in_viewport(driver: WebDriver, element) -> bool:
    """``element`` is fully inside the viewport, i.e. what a user can actually tap."""
    return driver.execute_script(
        "const r = arguments[0].getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight",
        element,
    )


def video_ready(driver: WebDriver) -> bool:
    """First ``<video>`` has a decoded frame to show (readyState >= HAVE_CURRENT_DATA)."""
    return driver.execute_script("const v = document.querySelector('video'); return !!v && v.readyState >= 2")


def viewport_images_loaded(driver: WebDriver) -> bool:
    """Every image intersecting the viewport has finished decoding.

    Off-screen images are skipped: lazy-loaded ones never load until scrolled to.
    """
    return driver.execute_script(
        """
        return [...document.images].every(img => {
          const r = img.getBoundingClientRect();
          const onScreen = r.width > 0 && r.bottom > 0 && r.top < innerHeight;
          return !onScreen || (img.complete && img.naturalWidth > 0);
        });
        """
    )
