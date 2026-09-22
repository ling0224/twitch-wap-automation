from __future__ import annotations

from typing import Self
from urllib.parse import urlparse

from selenium.webdriver.common.by import By

from src.core.waits import video_ready, viewport_images_loaded
from src.pages.twitch_page import TwitchPage


class StreamerPage(TwitchPage):
    """``/<login>``, reached by selecting a channel; there is no fixed path."""

    ready_locator = (By.TAG_NAME, "video") # <video playsinline="" webkit-playsinline="" aria-label="Twitch video player"></video>
    # ready_locator = (By.CSS_SELECTOR, '[data-a-target="video-player"]')
    CONTROLS_HIDDEN = (By.XPATH, '//button[normalize-space()="Show player controls"]')

    def wait_until_loaded(self) -> Self:
        """Base definition, plus: video has a frame and on-screen images are decoded.

        Player interstitials (e.g. a mature-content gate) can appear after the
        base pop-up pass and block playback, so pop-ups are re-checked on every
        poll until the video renders.
        """
        super().wait_until_loaded()
        print("wait for video rendered a frame")
        self.wait(self._video_ready_clearing_popups, "stream video never rendered a frame")
        print("wait for video rendered a frame and on-screen images decoded")
        self.wait(viewport_images_loaded, "on-screen images never finished decoding")
        return self

    def wait_for_player_controls_hidden(self) -> Self:
        """Wait for the player overlay to auto-hide (~5s after load) so it does not dim a screenshot.

        The toggle's label flips from "Hide player controls" to "Show player controls".
        """
        self.wait(
            lambda d: d.find_elements(*self.CONTROLS_HIDDEN),
            "player controls never auto-hid",
        )
        return self

    @property
    def streamer_login(self) -> str:
        return urlparse(self.driver.current_url).path.strip("/")

    def _video_ready_clearing_popups(self, driver) -> bool:
        if self.popups is not None:
            self.popups.dismiss_all()
        return video_ready(driver)
