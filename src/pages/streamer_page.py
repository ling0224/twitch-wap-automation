from __future__ import annotations

import logging
from typing import Self
from urllib.parse import urlparse

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from src.core.waits import video_ready, viewport_images_loaded
from src.pages.twitch_page import TwitchPage

log = logging.getLogger(__name__)

class StreamerPage(TwitchPage):
    """``/<login>``, reached by selecting a channel; there is no fixed path."""

    ready_locator = (By.TAG_NAME, "video")
    PLAYER_CONTROLS = (By.CSS_SELECTOR, '[data-a-target="player-controls"]')
    OVERLAY_CLICK_HANDLER = (By.CSS_SELECTOR, '[data-a-target="player-overlay-click-handler"]')

    def wait_until_loaded(self) -> Self:
        """Base definition, plus: video has a frame and on-screen images are decoded.

        Player interstitials (e.g. a mature-content gate) can appear after the
        base pop-up pass and block playback, so pop-ups are re-checked on every
        poll until the video renders.
        """
        super().wait_until_loaded()
        log.info("Waiting for the stream video to render a frame and finish decoding on-screen images")
        self.wait(self._video_ready_clearing_popups, "stream video never rendered a frame")
        self.wait(viewport_images_loaded, "on-screen images never finished decoding")
        return self

    def hide_player_controls(self) -> Self:
        """Collapse the player overlay so it does not dim a screenshot.

        On collapse ``player-controls`` flips to ``aria-hidden="true"``, fades
        out for ~0.1s and is then removed; only removal means nothing is left
        on screen. The overlay also auto-hides ~5s after load, so the tap is
        sent only while the controls are fully shown.
        """
        log.info("Hiding player controls before screenshot")

        def collapsed(driver) -> bool:
            controls = driver.find_elements(*self.PLAYER_CONTROLS)
            if not controls:
                return True
            try:
                shown = controls[0].get_attribute("aria-hidden") == "false"
            except StaleElementReferenceException:
                return False  # removed between find and read; the next poll sees it gone
            if shown:
                self.js_click(self.OVERLAY_CLICK_HANDLER)
            return False

        self.wait(collapsed, "player controls never collapsed")
        return self

    @property
    def streamer_login(self) -> str:
        return urlparse(self.driver.current_url).path.strip("/")

    def _video_ready_clearing_popups(self, driver) -> bool:
        if self.popups is not None:
            self.popups.dismiss_all()
        return video_ready(driver)
