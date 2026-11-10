"""Browser hook contracts from the professor's Fall 2026 BDD lab."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from features import environment


def browser_context():
    """Provide Behave's context interface without starting a browser."""
    cleanups = []
    context = SimpleNamespace(
        config=SimpleNamespace(
            userdata={"base_url": "http://unused.invalid", "wait_seconds": "1"},
            setup_logging=Mock(),
        ),
        add_cleanup=cleanups.append,
    )
    return context, cleanups


@pytest.mark.parametrize(
    "settings, expected_url, expected_wait, expected_browser",
    [
        ({}, "http://localhost:8080", 30, "chrome"),
        ({"BDD_BASE_URL": "http://wishlist:8080/"}, "http://wishlist:8080", 30, "chrome"),
        (
            {"BASE_URL": "http://localhost:8082/", "BDD_BASE_URL": "http://wishlist:8080"},
            "http://localhost:8082", 30, "chrome",
        ),
        (
            {"BASE_URL": "http://localhost:8081/", "WAIT_SECONDS": "7", "DRIVER": "FIREFOX"},
            "http://localhost:8081", 7, "firefox",
        ),
    ],
)
def test_browser_configuration(monkeypatch, settings, expected_url, expected_wait, expected_browser):
    """It should honor the course environment variables and browser interface."""
    for name in ("BASE_URL", "BDD_BASE_URL", "WAIT_SECONDS", "DRIVER"):
        monkeypatch.delenv(name, raising=False)
    for name, value in settings.items():
        monkeypatch.setenv(name, value)
    browsers = {"chrome": Mock(), "firefox": Mock()}
    monkeypatch.setattr(environment, "which", lambda name: "/test/geckodriver" if name == "geckodriver" else None)
    monkeypatch.setattr(environment.webdriver, "Chrome", Mock(return_value=browsers["chrome"]))
    monkeypatch.setattr(environment.webdriver, "Firefox", Mock(return_value=browsers["firefox"]))
    context, cleanups = browser_context()

    environment.before_all(context)

    assert context.base_url == expected_url
    assert context.wait_seconds == expected_wait
    assert context.driver is browsers[expected_browser]
    assert context.browser is context.driver
    if expected_browser == "firefox":
        arguments = environment.webdriver.Firefox.call_args.kwargs
        assert arguments["options"].preferences.get("devtools.jsonview.enabled") is False
        assert arguments["service"].path == "/test/geckodriver"
    context.driver.implicitly_wait.assert_called_once_with(expected_wait)
    context.driver.set_window_size.assert_called_once_with(1280, 1300)
    context.driver.set_page_load_timeout.assert_called_once_with(expected_wait)
    context.config.setup_logging.assert_called_once_with()
    assert len(cleanups) == 1
    cleanups[0]()
    context.driver.quit.assert_called_once_with()


def test_invalid_wait_does_not_launch_browser(monkeypatch):
    """It should reject a non-integer timeout before allocating a browser."""
    monkeypatch.setenv("WAIT_SECONDS", "invalid")
    launch = Mock()
    monkeypatch.setattr(environment.webdriver, "Chrome", launch)
    context, cleanups = browser_context()

    with pytest.raises(ValueError):
        environment.before_all(context)

    launch.assert_not_called()
    assert not cleanups


def test_browser_configuration_failure_keeps_cleanup(monkeypatch):
    """It should still close the browser if configuring its timeout fails."""
    monkeypatch.setenv("DRIVER", "chrome")
    monkeypatch.setenv("WAIT_SECONDS", "5")
    browser = Mock()
    browser.implicitly_wait.side_effect = RuntimeError("browser disconnected")
    monkeypatch.setattr(environment.webdriver, "Chrome", Mock(return_value=browser))
    context, cleanups = browser_context()

    with pytest.raises(RuntimeError, match="browser disconnected"):
        environment.before_all(context)

    assert len(cleanups) == 1
    cleanups[0]()
    browser.quit.assert_called_once_with()
