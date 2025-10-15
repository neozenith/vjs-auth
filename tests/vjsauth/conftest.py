"""
Pytest configuration and fixtures for vjsauth site testing.
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for testing."""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the vjsauth site."""
    return "http://localhost:5173"


@pytest.fixture
def page_with_console_logs(page: Page):
    """
    Enhanced page fixture that captures console messages.

    Usage:
        def test_example(page_with_console_logs):
            page, console_logs = page_with_console_logs
            page.goto("/")
            assert len([log for log in console_logs if log.type == "error"]) == 0
    """
    console_logs = []

    def handle_console(msg):
        console_logs.append(msg)

    page.on("console", handle_console)
    yield page, console_logs
    page.remove_listener("console", handle_console)


@pytest.fixture
def expect_no_console_errors(page: Page):
    """
    Fixture that automatically fails test if console errors are detected.

    Usage:
        def test_example(page, expect_no_console_errors):
            page.goto("/")
            # Test automatically fails if console errors occur
    """
    errors = []

    def handle_console(msg):
        if msg.type == "error":
            errors.append(msg.text)

    page.on("console", handle_console)
    yield page
    page.remove_listener("console", handle_console)

    if errors:
        pytest.fail(f"Console errors detected: {errors}")
