"""WAP scenario: search a category and open a live streamer.

The test reads as the six steps from the specification. All Selenium detail
lives in the page objects; if this file starts containing locators, the
abstraction has leaked.
"""

import pytest

from src.core.waits import viewport_width, video_ready

@pytest.mark.smoke
def test_home_is_wap_layout(home, settings):
    """Step 1: open the home page and confirm WAP layout."""
    assert home.driver.current_url.startswith(settings.base_url)
    assert viewport_width(home.driver) == settings.device.width


@pytest.mark.e2e
@pytest.mark.parametrize("scroll_times", [2])
@pytest.mark.parametrize("search_term", ["StarCraft II"])
def test_search_scroll_and_screenshot_streamer(home, screenshot, search_term, scroll_times):
    """Steps 1-6: search a game, scroll the results, open a streamer and screenshot the loaded page."""

    streamer = (
        home.open_search()
        .search_and_click(search_term)
        .scroll_times(scroll_times)
        .select_streamer()
    )

    streamer.assert_wap_layout()
    assert video_ready(streamer.driver), "streamer page video not ready yet"

    streamer.hide_player_controls()
    path = screenshot(f"streamer_{streamer.streamer_login}")
    assert path.stat().st_size > 0