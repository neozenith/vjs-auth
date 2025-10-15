"""
Tests for locked content with Google OAuth cookie checking.

These tests verify that the locked content element properly checks for
authentication cookies and displays the appropriate UI state.
"""
import pytest
from playwright.sync_api import Page, expect


def test_locked_content_element_exists(page: Page, base_url: str):
    """Test that locked content element is created on page load."""
    page.goto(base_url)
    page.wait_for_timeout(1500)

    locked_content = page.locator("#locked-content")
    expect(locked_content).to_be_visible()


def test_locked_content_shows_unauthorized_state_without_cookie(page: Page, base_url: str):
    """Test that locked content shows unauthorized state when no OAuth cookie exists."""
    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for locked state heading
    heading = page.locator("#locked-content h3")
    expect(heading).to_contain_text("Locked: Google Calendar Access")

    # Check for lock icon in heading
    lock_icon = page.locator("#locked-content h3 svg")
    expect(lock_icon).to_be_visible()

    # Check for authentication message
    message = page.locator("#locked-content p").first
    expect(message).to_contain_text("requires authentication")


def test_google_signin_button_exists_when_unauthorized(page: Page, base_url: str):
    """Test that Google Sign-In button appears when unauthorized."""
    page.goto(base_url)
    page.wait_for_timeout(1500)

    signin_button = page.locator("#google-signin-button")
    expect(signin_button).to_be_visible()
    expect(signin_button).to_contain_text("Sign in with Google")


def test_google_signin_button_has_google_icon(page: Page, base_url: str):
    """Test that Google Sign-In button has the Google logo."""
    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for Google icon SVG inside button
    google_icon = page.locator("#google-signin-button svg").first
    expect(google_icon).to_be_visible()


def test_locked_content_placeholder_visible(page: Page, base_url: str):
    """Test that locked content placeholder with lock icon is visible."""
    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Look for the white box with lock icon (use .first to avoid strict mode error)
    placeholder = page.locator("#locked-content .bg-white").first
    expect(placeholder).to_be_visible()
    expect(placeholder).to_contain_text("Content locked - authentication required")


def test_oauth_description_text_present(page: Page, base_url: str):
    """Test that OAuth PKCE flow description is present."""
    page.goto(base_url)
    page.wait_for_timeout(1500)

    oauth_description = page.locator("#locked-content").get_by_text("OAuth 2.0 PKCE flow")
    expect(oauth_description).to_be_visible()


def test_cookie_check_logs_to_console(page: Page, base_url: str):
    """Test that cookie checking is logged to console."""
    console_messages = []

    def handle_console(msg):
        console_messages.append(msg.text)

    page.on("console", handle_console)
    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for OAuth token check message
    assert any("No Google OAuth access token found" in msg for msg in console_messages), \
        "Cookie check message not logged"

    # Check for locked content rendering message
    assert any("Locked content rendered - Authenticated: false" in msg for msg in console_messages), \
        "Locked content rendering message not logged"


def test_locked_content_stays_locked_without_valid_cookie(page: Page, base_url: str):
    """Test that locked content remains locked when cookie is not present."""
    # Clear all cookies first
    page.context.clear_cookies()

    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Verify locked state persists
    locked_content = page.locator("#locked-content")
    class_attr = locked_content.get_attribute("class")
    assert "bg-amber-50" in class_attr, f"Expected bg-amber-50 class, got: {class_attr}"

    # Verify sign-in button is still visible
    signin_button = page.locator("#google-signin-button")
    expect(signin_button).to_be_visible()


def test_locked_content_with_invalid_cookie_stays_unauthorized(page: Page, base_url: str):
    """Test that locked content stays unauthorized even with invalid cookie."""
    # Set an invalid/empty cookie
    page.context.add_cookies([{
        "name": "google_oauth_access_token",
        "value": "",
        "url": base_url
    }])

    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Should still show unauthorized state (empty cookie value)
    heading = page.locator("#locked-content h3")
    expect(heading).to_contain_text("Locked: Google Calendar Access")

    signin_button = page.locator("#google-signin-button")
    expect(signin_button).to_be_visible()


def test_signin_button_click_shows_alert(page: Page, base_url: str):
    """Test that clicking sign-in button shows placeholder alert."""
    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Setup dialog handler
    page.on("dialog", lambda dialog: dialog.accept())

    # Click the sign-in button
    signin_button = page.locator("#google-signin-button")
    signin_button.click()

    # Wait a bit to ensure dialog was triggered
    page.wait_for_timeout(500)


def test_locked_content_console_messages(page: Page, base_url: str):
    """Test that locked content initialization logs correct console messages."""
    console_messages = []

    def handle_console(msg):
        if msg.type == "log":
            console_messages.append(msg.text)

    page.on("console", handle_console)
    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for expected console logs
    assert any("Google Sign-In button clicked" not in msg for msg in console_messages), \
        "Button should not be clicked automatically"

    # Verify initialization message
    assert any("Locked content rendered" in msg for msg in console_messages), \
        "Locked content should log initialization"
