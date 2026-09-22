from __future__ import annotations

from selenium.webdriver.common.by import By
from src.core.base_page import Locator

from src.pages.search_results_page import SearchResultsPage
from src.pages.category_page import CategoryPage
from src.pages.twitch_page import TwitchPage

class SearchPage(TwitchPage):
    # use for go_to() if we start the flow at SearchPage instead of HomePage
    path = "/directory"

    SEARCH_INPUT = (By.CSS_SELECTOR, 'input[data-a-target="tw-input"]')
    ready_locator = SEARCH_INPUT

    @staticmethod
    def category_suggestion(term: str) -> Locator:
        """The game (category) entry in the suggestion list whose name is exactly ``term``."""
        return (By.XPATH, f'//a[starts-with(@href, "/directory/category/") and normalize-space()="{term}"]')

    def search_and_click(self, term: str) -> SearchResultsPage:
        """Type ``term`` and pick the matching game from the suggestions, instead of using SendKeys(ENTER)
        """
        self.type_text(self.SEARCH_INPUT, term)
        self.wait_and_click(self.category_suggestion(term))
        return self.go_to(SearchResultsPage)