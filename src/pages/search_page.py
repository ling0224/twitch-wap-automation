from __future__ import annotations

from urllib.parse import quote

from selenium.webdriver.common.by import By

from src.core.base_page import Locator
from src.pages.search_results_page import SearchResultsPage
from src.pages.twitch_page import TwitchPage


class SearchPage(TwitchPage):
    # use for go_to() if we start the flow at SearchPage instead of HomePage
    path = "/directory"

    SEARCH_INPUT = (By.CSS_SELECTOR, 'input[data-a-target="tw-input"]')
    ready_locator = SEARCH_INPUT

    @staticmethod
    def first_suggestion(term: str) -> Locator:
        """First real suggestion for exactly ``term``.

        The list items carry no attributes. The list always ends with a fixed
        "search for <term>" entry (``/search?term=<term>``) and "Go to <term>";
        real suggestions load asynchronously and are inserted *before* them.
        Anchoring on items preceding that entry therefore (a) pins the list to
        the full term, not a stale partial one, and (b) matches nothing until
        the real suggestions have arrived, so the wait cannot click too early.
        """
        search_href = f"/search?term={quote(term, safe='')}"
        return (By.XPATH, f'(//ul/li[following-sibling::li/a[@href="{search_href}"]]/a)[1]')

    def search_and_click(self, term: str) -> SearchResultsPage:
        """Type ``term`` and open the first suggestion, instead of pressing Enter.

        For a game name such as "StarCraft II" the first suggestion is the
        game's category page (a term like "sc2" would lead to a channel instead).
        """
        self.type_text(self.SEARCH_INPUT, term)
        self.wait_and_click(self.first_suggestion(term))
        return self.go_to(SearchResultsPage)
