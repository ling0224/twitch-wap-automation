from __future__ import annotations

from typing import Self

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from src.core.retry import retry_on_transient
from src.core.waits import in_viewport
from src.pages.twitch_page import TwitchPage


class SearchResultsPage(TwitchPage):
    """``/directory/category/") and normalize-space()="{term}"``: live streams of one game, reached from a search suggestion."""

    LINK_CARD = (By.XPATH, '//button[contains(@class, "tw-link")]')
    ready_locator = LINK_CARD

    def scroll_times(self, times: int) -> Self:
        """Scroll ``times`` viewports, recursively: scroll one full viewport,
        wait until cards are rendered there, then solve ``times - 1``.

        The list is infinite (the next page loads only once the bottom is
        reached) and virtualised (card count goes 9 -> 8 -> 14), so progress is
        measured by scroll position, not by card count.
        """
        if times <= 0:
            return self
        self.scroll_one_viewport()
        self.wait(lambda _: self._cards_on_screen(), "no channel card rendered after scrolling")
        return self.scroll_times(times - 1)

    @retry_on_transient()
    def _click_card(self, index: int) -> None:
        # Find + click are retried together: a recycled card must be re-found, not re-clicked.
        cards = self._cards_on_screen()
        if index >= len(cards):
            raise AssertionError(f"only {len(cards)} channel card(s) on screen, wanted index {index}")
        self.scroll_into_view(cards[index])
        cards[index].click()

    def _cards_on_screen(self) -> list[WebElement]:
        cards = []
        for card in self.find_all(self.LINK_CARD):
            try:
                if in_viewport(self.driver, card):
                    cards.append(card)
            except StaleElementReferenceException:
                continue  # node recycled between find and check; it is no longer that card
        return cards