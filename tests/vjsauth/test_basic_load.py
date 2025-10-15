"""
Basic loading tests for vjsauth site.

These tests verify that the site loads correctly without errors.
"""
import pytest
from playwright.sync_api import Page, expect


def test_page_loads_successfully(page: Page, base_url: str):
    """Test that the page loads without 404 or server errors."""
    response = page.goto(base_url)
    assert response is not None, "Failed to load page"
    assert response.status < 400, f"HTTP error: {response.status}"


def test_no_console_errors(page: Page, base_url: str):
    """Test that page loads without console errors."""
    console_errors = []

    def handle_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)

    page.on("console", handle_console)
    page.goto(base_url)

    # Wait a bit for any delayed errors
    page.wait_for_timeout(1000)

    assert len(console_errors) == 0, f"Console errors detected: {console_errors}"


def test_page_title_exists(page: Page, base_url: str):
    """Test that the page has a title."""
    page.goto(base_url)
    title = page.title()
    assert title is not None and title != "", "Page title is missing"


def test_page_renders_content(page: Page, base_url: str):
    """Test that the page renders some content (not blank)."""
    page.goto(base_url)

    # Check if body has content
    body_content = page.locator("body").inner_text()
    assert len(body_content.strip()) > 0, "Page body is empty"


def test_script_loads_and_executes(page: Page, base_url: str):
    """Test that script.js loads and executes successfully."""
    console_messages = []

    def handle_console(msg):
        console_messages.append(msg.text)

    page.on("console", handle_console)
    page.goto(base_url)

    # Wait for script to execute
    page.wait_for_timeout(1000)

    # Check for expected console messages from script.js
    assert any("script.js loaded successfully" in msg for msg in console_messages), \
        "Script.js initialization message not found in console"


def test_script_modifies_dom(page: Page, base_url: str):
    """Test that script.js dynamically modifies the DOM."""
    page.goto(base_url)

    # Wait for script to add dynamic content
    page.wait_for_timeout(1500)

    # Check for the dynamically added status item
    status_items = page.locator("#status-container li").all_inner_texts()
    assert any("JavaScript loaded and executed" in item for item in status_items), \
        "Script did not add expected status item to DOM"


def test_interactive_button_created(page: Page, base_url: str):
    """Test that script.js creates the interactive demo button."""
    page.goto(base_url)

    # Wait for script to add interactive features
    page.wait_for_timeout(1500)

    # Check for the interactive button
    demo_button = page.locator("#demo-button")
    expect(demo_button).to_be_visible()
    expect(demo_button).to_contain_text("Click Me!")


def test_timestamp_added(page: Page, base_url: str):
    """Test that script.js adds a timestamp."""
    page.goto(base_url)

    # Wait for script to add timestamp
    page.wait_for_timeout(1500)

    # Check for timestamp container
    timestamp = page.locator("#timestamp")
    timestamp_text = timestamp.inner_text()
    assert "Script executed:" in timestamp_text, "Timestamp not added by script"


def test_tailwind_css_loaded(page: Page, base_url: str):
    """Test that Tailwind CSS is loaded and applied."""
    page.goto(base_url)

    # Wait for Tailwind to load
    page.wait_for_timeout(1000)

    # Check if Tailwind classes are applied by checking computed styles
    container = page.locator(".container").first
    bg_color = container.evaluate("el => window.getComputedStyle(el).backgroundColor")

    # White background should be applied (rgb(255, 255, 255))
    assert bg_color == "rgb(255, 255, 255)" or "255" in bg_color, \
        "Tailwind CSS styles not applied correctly"
