"""Retry helper for genuinely transient Selenium failures.

Scoped deliberately narrowly: only stale references and intercepted clicks,
which are re-render artefacts rather than real defects. Broad retries hide bugs.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, TypeVar

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)

log = logging.getLogger(__name__)

TRANSIENT = (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)

T = TypeVar("T")


def retry_on_transient(attempts: int = 3, delay: float = 0.5) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except TRANSIENT as exc:
                    last_error = exc
                    log.debug(
                        "%s failed (attempt %s/%s): %s",
                        func.__name__,
                        attempt,
                        attempts,
                        type(exc).__name__,
                    )
                    time.sleep(delay)
            raise AssertionError(
                f"{func.__name__} failed after {attempts} attempts"
            ) from last_error

        return wrapper

    return decorator
