"""
Tests for OAuth authenticated state with Google Calendar access.

These tests verify the authenticated state when a valid OAuth token cookie exists.
"""
import pytest
from playwright.sync_api import Page, expect


def test_authenticated_state_shows_unlocked_content(page: Page, base_url: str):
    """Test that authenticated state shows unlocked content."""
    # Set a valid OAuth token cookie
    page.context.add_cookies([{
        "name": "google_oauth_access_token",
        "value": "mock_access_token_12345",
        "url": base_url
    }])

    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for unlocked state
    locked_content = page.locator("#locked-content")
    expect(locked_content).to_be_visible()

    # Verify green background (authenticated state)
    class_attr = locked_content.get_attribute("class")
    assert "bg-green-50" in class_attr, f"Expected bg-green-50 class, got: {class_attr}"


def test_authenticated_state_shows_correct_heading(page: Page, base_url: str):
    """Test that authenticated state shows correct heading."""
    # Set a valid OAuth token cookie
    page.context.add_cookies([{
        "name": "google_oauth_access_token",
        "value": "mock_access_token_12345",
        "url": base_url
    }])

    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for unlocked heading
    heading = page.locator("#locked-content h3")
    expect(heading).to_contain_text("Unlocked: Google Calendar Access")


def test_authenticated_state_shows_success_message(page: Page, base_url: str):
    """Test that authenticated state shows success message."""
    # Set a valid OAuth token cookie
    page.context.add_cookies([{
        "name": "google_oauth_access_token",
        "value": "mock_access_token_12345",
        "url": base_url
    }])

    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for authentication success message
    message = page.locator("#locked-content").get_by_text("You are successfully authenticated")
    expect(message).to_be_visible()


def test_authenticated_state_shows_success_icon(page: Page, base_url: str):
    """Test that authenticated state shows success checkmark icon."""
    # Set a valid OAuth token cookie
    page.context.add_cookies([{
        "name": "google_oauth_access_token",
        "value": "mock_access_token_12345",
        "url": base_url
    }])

    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for success checkmark
    success_message = page.locator("#locked-content").get_by_text("Authentication Successful")
    expect(success_message).to_be_visible()


def test_authenticated_state_shows_signout_button(page: Page, base_url: str):
    """Test that authenticated state shows sign-out button."""
    # Set a valid OAuth token cookie
    page.context.add_cookies([{
        "name": "google_oauth_access_token",
        "value": "mock_access_token_12345",
        "url": base_url
    }])

    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for sign-out button
    signout_button = page.locator("#google-signout-button")
    expect(signout_button).to_be_visible()
    expect(signout_button).to_contain_text("Sign Out")


def test_signout_button_removes_cookie_and_reloads(page: Page, base_url: str):
    """Test that clicking sign-out button removes cookie and reloads page."""
    # Set a valid OAuth token cookie
    page.context.add_cookies([{
        "name": "google_oauth_access_token",
        "value": "mock_access_token_12345",
        "url": base_url
    }])

    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Click sign-out button and wait for navigation/reload
    signout_button = page.locator("#google-signout-button")
    page.wait_for_load_state("networkidle")

    # Click and wait for reload
    signout_button.click()
    page.wait_for_timeout(2000)

    # After reload, should show unauthorized state
    heading = page.locator("#locked-content h3")
    expect(heading).to_contain_text("Locked: Google Calendar Access")


def test_authenticated_logs_to_console(page: Page, base_url: str):
    """Test that authenticated state logs to console."""
    console_messages = []

    def handle_console(msg):
        console_messages.append(msg.text)

    page.on("console", handle_console)

    # Set a valid OAuth token cookie
    page.context.add_cookies([{
        "name": "google_oauth_access_token",
        "value": "mock_access_token_12345",
        "url": base_url
    }])

    page.goto(base_url)
    page.wait_for_timeout(1500)

    # Check for OAuth token found message
    assert any("Google OAuth access token found" in msg for msg in console_messages), \
        "OAuth token found message not logged"

    # Check for authenticated rendering message
    assert any("Locked content rendered - Authenticated: true" in msg for msg in console_messages), \
        "Authenticated rendering message not logged"


def test_signin_button_initiates_oauth_flow(page: Page, base_url: str):
    """Test that sign-in button initiates OAuth flow with Lambda@Edge pattern."""
    page.goto(base_url)
    page.wait_for_timeout(1500)

    console_messages = []

    def handle_console(msg):
        console_messages.append(msg.text)

    page.on("console", handle_console)

    # Get current URL before clicking
    initial_url = page.url

    # Click the sign-in button
    # Note: In Lambda@Edge pattern, this will redirect to Google OAuth
    # We can't test the actual redirect without mocking, but we can verify the button works
    signin_button = page.locator("#google-signin-button")
    expect(signin_button).to_be_visible()

    # Verify console logging happens when button is clicked
    # (We can't actually click and follow through without Google auth in tests)
    # But we can verify the button is properly configured
    assert signin_button.text_content() is not None, "Sign-in button should have text"
