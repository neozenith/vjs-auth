/**
 * VJS Auth - Main JavaScript
 *
 * This script dynamically updates the page to demonstrate successful loading.
 */

(function () {
  "use strict";

  // Log initialization
  console.log("VJS Auth script.js loaded successfully");
  console.log("Port: 5173");
  console.log("Ready for iterative development");

  /**
   * Cookie management utilities
   */
  const CookieManager = {
    /**
     * Get a cookie value by name
     * @param {string} name - Cookie name
     * @returns {string|null} Cookie value or null if not found
     */
    getCookie(name) {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) {
        return parts.pop().split(";").shift();
      }
      return null;
    },

    /**
     * Set a cookie
     * @param {string} name - Cookie name
     * @param {string} value - Cookie value
     * @param {number} days - Expiration in days
     */
    setCookie(name, value, days = 7) {
      const date = new Date();
      date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
      const expires = `expires=${date.toUTCString()}`;
      document.cookie = `${name}=${value};${expires};path=/;SameSite=Lax`;
    },

    /**
     * Delete a cookie
     * @param {string} name - Cookie name
     */
    deleteCookie(name) {
      document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    },

    /**
     * Check if Google OAuth access token exists
     * @returns {boolean} True if token exists, false otherwise
     */
    hasGoogleOAuthToken() {
      const token = this.getCookie("google_oauth_access_token");
      if (token) {
        console.log("Google OAuth access token found in cookies");
        return true;
      }
      console.log("No Google OAuth access token found");
      return false;
    },

    /**
     * Get Google OAuth access token
     * @returns {string|null} Token value or null
     */
    getGoogleOAuthToken() {
      return this.getCookie("google_oauth_access_token");
    },
  };

  /**
   * Initialize the application when DOM is ready
   */
  function init() {
    console.log("Initializing VJS Auth...");

    // Update status indicator
    updateStatusIndicator();

    // Add dynamic timestamp
    addTimestamp();

    // Add interactive features
    addInteractiveFeatures();

    // Add locked content section
    addLockedContent();

    console.log("VJS Auth initialized successfully");
  }

  /**
   * Update the status indicator to show script loaded
   */
  function updateStatusIndicator() {
    const statusContainer = document.getElementById("status-container");
    if (!statusContainer) return;

    // Create new status item
    const statusItem = document.createElement("li");
    statusItem.className = "animate-fade-in";
    statusItem.innerHTML = "✓ JavaScript loaded and executed";

    statusContainer.appendChild(statusItem);
  }

  /**
   * Add timestamp to show when script executed
   */
  function addTimestamp() {
    const timestampContainer = document.getElementById("timestamp");
    if (!timestampContainer) return;

    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const dateString = now.toLocaleDateString();

    timestampContainer.innerHTML = `
            <div class="text-sm text-gray-600 mt-4 p-3 bg-gray-50 rounded-lg">
                <strong>Script executed:</strong> ${dateString} at ${timeString}
            </div>
        `;
  }

  /**
   * Add interactive features to demonstrate dynamic capabilities
   */
  function addInteractiveFeatures() {
    // Add click counter to demonstrate interactivity
    const container = document.querySelector(".container");
    if (!container) return;

    let clickCount = 0;

    const clickCounter = document.createElement("div");
    clickCounter.id = "click-counter";
    clickCounter.className = "mt-6 p-4 bg-indigo-50 rounded-lg border-l-4 border-indigo-500";
    clickCounter.innerHTML = `
            <h3 class="text-indigo-700 font-semibold mb-2">Interactive Demo</h3>
            <p class="text-gray-700 mb-3">Click the button to test dynamic updates:</p>
            <button
                id="demo-button"
                class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
                Click Me! (Count: <span id="click-count">0</span>)
            </button>
        `;

    container.appendChild(clickCounter);

    // Add click handler
    const demoButton = document.getElementById("demo-button");
    const clickCountSpan = document.getElementById("click-count");

    if (demoButton && clickCountSpan) {
      demoButton.addEventListener("click", function () {
        clickCount++;
        clickCountSpan.textContent = clickCount;
        console.log(`Button clicked ${clickCount} time(s)`);

        // Add visual feedback
        this.classList.add("scale-95");
        setTimeout(() => {
          this.classList.remove("scale-95");
        }, 100);
      });
    }
  }

  /**
   * Add locked content section with Google OAuth integration
   */
  function addLockedContent() {
    const container = document.querySelector(".container");
    if (!container) return;

    // Check for OAuth token
    const isAuthenticated = CookieManager.hasGoogleOAuthToken();
    const token = CookieManager.getGoogleOAuthToken();

    // Create locked content container
    const lockedContentDiv = document.createElement("div");
    lockedContentDiv.id = "locked-content";
    lockedContentDiv.className = "mt-6 p-6 bg-amber-50 rounded-lg border-l-4 border-amber-500";

    if (isAuthenticated && token) {
      // Authenticated state (future implementation)
      lockedContentDiv.innerHTML = `
                <h3 class="text-amber-700 font-semibold mb-3 flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"></path>
                    </svg>
                    Google Calendar Access
                </h3>
                <p class="text-gray-700 mb-3">You are authenticated! Future calendar features will appear here.</p>
            `;
    } else {
      // Unauthorized state - showing lock icon and sign-in button
      lockedContentDiv.innerHTML = `
                <h3 class="text-amber-700 font-semibold mb-3 flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                    </svg>
                    Locked: Google Calendar Access
                </h3>
                <p class="text-gray-700 mb-4">
                    This content requires authentication with your Google account to access Google Calendar features.
                </p>
                <div class="bg-white p-4 rounded-lg mb-4">
                    <div class="flex items-center justify-center text-gray-400 py-8">
                        <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path>
                        </svg>
                    </div>
                    <p class="text-center text-gray-500 text-sm">Content locked - authentication required</p>
                </div>
                <button
                    id="google-signin-button"
                    class="w-full bg-white hover:bg-gray-50 text-gray-700 font-medium py-3 px-6 rounded-lg border-2 border-gray-300 transition-colors duration-200 flex items-center justify-center"
                >
                    <svg class="w-5 h-5 mr-3" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                    Sign in with Google
                </button>
                <p class="text-xs text-gray-500 mt-3 text-center">
                    Clicking this button will initiate a secure OAuth 2.0 PKCE flow with Google
                </p>
            `;

      // Add click handler for sign-in button (placeholder for future PKCE implementation)
      setTimeout(() => {
        const signInButton = document.getElementById("google-signin-button");
        if (signInButton) {
          signInButton.addEventListener("click", function () {
            console.log("Google Sign-In button clicked");
            console.log("PKCE OAuth flow will be implemented in future iteration");
            alert("Google OAuth PKCE flow not yet implemented.\n\nThis button is ready for future OAuth integration.");
          });
        }
      }, 100);
    }

    container.appendChild(lockedContentDiv);
    console.log(`Locked content rendered - Authenticated: ${isAuthenticated}`);
  }

  /**
   * Wait for DOM to be ready, then initialize
   */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    // DOM is already ready
    init();
  }
})();
