from __future__ import annotations

from selenium.webdriver.common.by import By

from src.pages.search_page import SearchPage
from src.pages.twitch_page import TwitchPage

class HomePage(TwitchPage):
    path = "/"
    ready_locator = (By.CSS_SELECTOR, 'a[aria-label="Go to the Twitch home page"]') 

    SEARCH_ICON = (By.XPATH, '//a[@href="/directory"][.//*[local-name()="svg"]]')

    def open_search(self) -> SearchPage:
        if self.SEARCH_ICON is None:
            raise NotImplementedError("HomePage.SEARCH_ICON is not set yet")
        self.wait_and_click(self.SEARCH_ICON)
        return self.go_to(SearchPage)