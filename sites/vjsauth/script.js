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
   * OAuth Configuration
   * IMPORTANT: Client ID is public, but client_secret must stay on Lambda@Edge
   *
   * Lambda@Edge Pattern (Unified Server):
   * - Single server handles both static files AND OAuth callback
   * - Frontend redirects to Google OAuth
   * - Google redirects back to /oauth/callback (same host!)
   * - Server exchanges code for token (has client_secret)
   * - Server sets cookie and redirects back to /
   *
   * This mimics production CloudFront + Lambda@Edge architecture.
   *
   * Configuration is loaded dynamically from config.json at runtime.
   */
  let OAuthConfig = null;

  /**
   * Load OAuth configuration from config.json
   * @returns {Promise<Object>} OAuth configuration object
   */
  async function loadConfig() {
    try {
      const response = await fetch("/config.json");
      if (!response.ok) {
        throw new Error(`Failed to load config: ${response.status}`);
      }
      const config = await response.json();

      // Build OAuth configuration from loaded config
      OAuthConfig = {
        clientId: config.oauth.clientId,
        redirectUri: window.location.origin + config.oauth.redirectPath,
        authorizationEndpoint: config.oauth.authorizationEndpoint,
        scopes: config.oauth.scopes,
      };

      console.log("OAuth configuration loaded successfully");
      console.log("Client ID:", OAuthConfig.clientId);
      console.log("Redirect URI:", OAuthConfig.redirectUri);

      return OAuthConfig;
    } catch (error) {
      console.error("Failed to load configuration:", error);
      throw error;
    }
  }

  /**
   * PKCE Utilities for OAuth 2.0 Authorization Code Flow
   */
  const PKCEUtils = {
    /**
     * Generate a random code verifier for PKCE
     * @returns {string} Base64 URL-encoded random string
     */
    generateCodeVerifier() {
      const array = new Uint8Array(32);
      crypto.getRandomValues(array);
      return this.base64UrlEncode(array);
    },

    /**
     * Generate code challenge from verifier using SHA-256
     * @param {string} verifier - The code verifier
     * @returns {Promise<string>} Base64 URL-encoded SHA-256 hash
     */
    async generateCodeChallenge(verifier) {
      const encoder = new TextEncoder();
      const data = encoder.encode(verifier);
      const hash = await crypto.subtle.digest("SHA-256", data);
      return this.base64UrlEncode(new Uint8Array(hash));
    },

    /**
     * Generate random state parameter for CSRF protection
     * @returns {string} Random state string
     */
    generateState() {
      const array = new Uint8Array(16);
      crypto.getRandomValues(array);
      return this.base64UrlEncode(array);
    },

    /**
     * Base64 URL-encode a byte array
     * @param {Uint8Array} buffer - Byte array to encode
     * @returns {string} Base64 URL-encoded string
     */
    base64UrlEncode(buffer) {
      const base64 = btoa(String.fromCharCode(...buffer));
      return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
    },
  };

  /**
   * OAuth Manager for Lambda@Edge pattern
   */
  const OAuthManager = {
    /**
     * Initiate OAuth PKCE flow with Lambda@Edge callback
     *
     * Lambda@Edge Pattern:
     * 1. Generate PKCE parameters
     * 2. Encode code_verifier in state parameter
     * 3. Redirect to Google OAuth with Lambda@Edge callback URL
     * 4. Google redirects to Lambda@Edge with state containing code_verifier
     * 5. Lambda@Edge extracts code_verifier from state and exchanges token
     */
    async initiateOAuthFlow() {
      console.log("Initiating OAuth PKCE flow (Lambda@Edge pattern)...");

      // Generate PKCE parameters
      const codeVerifier = PKCEUtils.generateCodeVerifier();
      const codeChallenge = await PKCEUtils.generateCodeChallenge(codeVerifier);
      const csrfToken = PKCEUtils.generateState();

      // Encode code_verifier in state parameter
      // State will be: base64(JSON({csrf: xxx, verifier: xxx}))
      const stateData = {
        csrf: csrfToken,
        verifier: codeVerifier,
      };
      const stateJson = JSON.stringify(stateData);
      const state = btoa(stateJson);

      // Store CSRF token for validation
      sessionStorage.setItem("oauth_csrf", csrfToken);

      console.log("PKCE parameters generated");
      console.log("State contains both CSRF token and code_verifier");

      // Build authorization URL
      // IMPORTANT: redirect_uri must match EXACTLY what's in Google Cloud Console
      const params = new URLSearchParams({
        client_id: OAuthConfig.clientId,
        redirect_uri: OAuthConfig.redirectUri,
        response_type: "code",
        scope: OAuthConfig.scopes.join(" "),
        state: state,
        code_challenge: codeChallenge,
        code_challenge_method: "S256",
        access_type: "offline",
        prompt: "consent",
      });

      const authUrl = `${OAuthConfig.authorizationEndpoint}?${params.toString()}`;
      console.log("Redirecting to Google OAuth...");
      console.log("Redirect URI:", OAuthConfig.redirectUri);
      console.log("Authorization URL:", authUrl);

      // Redirect to Google OAuth
      window.location.href = authUrl;
    },

    /**
     * Check for OAuth callback errors
     *
     * Lambda@Edge Pattern:
     * Lambda@Edge handles the entire callback, token exchange, and cookie setting.
     * The frontend only needs to check for errors and clean up.
     */
    async handleOAuthCallback() {
      const urlParams = new URLSearchParams(window.location.search);
      const oauthError = urlParams.get("oauth_error");

      // Check if Lambda@Edge redirected with an error
      if (oauthError) {
        console.error("OAuth error from Lambda@Edge:", oauthError);
        let errorMessage = "OAuth authentication failed";

        switch (oauthError) {
          case "no_code":
            errorMessage = "No authorization code received from Google";
            break;
          case "no_verifier":
            errorMessage = "PKCE code verifier missing";
            break;
          case "server_config":
            errorMessage = "Server configuration error (client_secret not set)";
            break;
          case "token_exchange_failed":
            errorMessage = "Failed to exchange authorization code for token";
            break;
          case "internal_error":
            errorMessage = "Internal server error during OAuth";
            break;
        }

        alert(`OAuth Error: ${errorMessage}`);
        this.cleanupOAuthState();

        // Clean URL
        const cleanUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);

        return false;
      }

      // Check if we just came back from OAuth (Lambda@Edge set the cookie)
      // No code parameter because Lambda@Edge already processed it
      const hasToken = CookieManager.hasGoogleOAuthToken();
      const storedCsrf = sessionStorage.getItem("oauth_csrf");

      if (hasToken && storedCsrf) {
        console.log("OAuth callback processed by Lambda@Edge successfully");
        this.cleanupOAuthState();

        // Clean URL
        const cleanUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);

        return true;
      }

      return false; // Not an OAuth callback
    },

    /**
     * Clean up OAuth state from sessionStorage
     */
    cleanupOAuthState() {
      sessionStorage.removeItem("oauth_csrf");
      console.log("OAuth state cleaned up");
    },
  };

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
   * Google Calendar API Manager
   */
  const CalendarManager = {
    /**
     * List all calendars for the authenticated user
     * @returns {Promise<Array>} Array of calendar objects
     */
    async listCalendars() {
      const token = CookieManager.getGoogleOAuthToken();
      if (!token) {
        throw new Error("No access token available");
      }

      const response = await fetch("https://www.googleapis.com/calendar/v3/users/me/calendarList", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to fetch calendars: ${errorData.error.message}`);
      }

      const data = await response.json();
      return data.items || [];
    },

    /**
     * Find a calendar by name (summary)
     * @param {string} calendarName - Name of the calendar to find
     * @returns {Promise<Object|null>} Calendar object or null if not found
     */
    async findCalendarByName(calendarName) {
      const calendars = await this.listCalendars();
      return calendars.find((cal) => cal.summary === calendarName) || null;
    },

    /**
     * Get events from a calendar
     * @param {string} calendarId - Calendar ID
     * @param {Object} options - Query options
     * @returns {Promise<Array>} Array of event objects
     */
    async getEvents(calendarId, options = {}) {
      const token = CookieManager.getGoogleOAuthToken();
      if (!token) {
        throw new Error("No access token available");
      }

      const params = new URLSearchParams({
        singleEvents: "true",
        orderBy: "startTime",
        ...options,
      });

      const response = await fetch(
        `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendarId)}/events?${params}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Failed to fetch events: ${errorData.error.message}`);
      }

      const data = await response.json();
      return data.items || [];
    },

    /**
     * Get recent past events
     * @param {string} calendarId - Calendar ID
     * @param {number} maxResults - Maximum number of events
     * @returns {Promise<Array>} Array of past event objects
     */
    async getRecentPastEvents(calendarId, maxResults = 5) {
      const now = new Date().toISOString();
      const events = await this.getEvents(calendarId, {
        timeMax: now,
        maxResults: maxResults,
      });
      // Reverse to get most recent first
      return events.reverse();
    },

    /**
     * Get upcoming future events
     * @param {string} calendarId - Calendar ID
     * @param {number} maxResults - Maximum number of events
     * @returns {Promise<Array>} Array of future event objects
     */
    async getUpcomingEvents(calendarId, maxResults = 3) {
      const now = new Date().toISOString();
      return await this.getEvents(calendarId, {
        timeMin: now,
        maxResults: maxResults,
      });
    },

    /**
     * Format event for display
     * @param {Object} event - Calendar event object
     * @param {Object} previousEvent - Previous event for calculating days since
     * @returns {string} Formatted HTML string
     */
    formatEvent(event, previousEvent = null) {
      const start = event.start.dateTime || event.start.date;
      const end = event.end.dateTime || event.end.date;

      const startDate = new Date(start);
      const endDate = new Date(end);

      const formatDateTime = (date) => {
        return date.toLocaleString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
          hour: "numeric",
          minute: "2-digit",
        });
      };

      // Calculate days since previous event
      let daysSincePrevious = null;
      if (previousEvent) {
        const previousStart = new Date(previousEvent.start.dateTime || previousEvent.start.date);
        const diffTime = Math.abs(startDate - previousStart);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        daysSincePrevious = diffDays;
      }

      return `
        <div class="border-l-2 border-indigo-300 pl-3 py-2 flex justify-between items-start">
          <div class="flex-1">
            <div class="font-semibold text-gray-800">${event.summary || "Untitled Event"}</div>
            <div class="text-sm text-gray-600">
              ${formatDateTime(startDate)}
              ${event.start.dateTime ? ` - ${endDate.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}` : ""}
            </div>
            ${event.location ? `<div class="text-xs text-gray-500 mt-1">📍 ${event.location}</div>` : ""}
          </div>
          ${
            daysSincePrevious !== null
              ? `<div class="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-1 rounded ml-4 whitespace-nowrap">
                  ${daysSincePrevious} ${daysSincePrevious === 1 ? "day" : "days"}
                </div>`
              : ""
          }
        </div>
      `;
    },
  };

  /**
   * Initialize the application when DOM is ready
   */
  async function init() {
    console.log("Initializing VJS Auth (Lambda@Edge pattern)...");

    // Load OAuth configuration first
    try {
      await loadConfig();
    } catch (error) {
      console.error("Failed to initialize: Could not load configuration");
      alert("Configuration Error: Unable to load OAuth settings. Please check console for details.");
      return;
    }

    // Check for OAuth callback errors or completion
    // Lambda@Edge handles the redirect back, so we just check and clean up
    await OAuthManager.handleOAuthCallback();

    // Add locked content section
    addLockedContent();

    console.log("VJS Auth initialized successfully");
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
      // Authenticated state - show unlocked content
      lockedContentDiv.className = "mt-6 p-6 bg-green-50 rounded-lg border-l-4 border-green-500";
      lockedContentDiv.innerHTML = `
                <h3 class="text-green-700 font-semibold mb-3 flex items-center">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"></path>
                    </svg>
                    Unlocked: Google Calendar Access
                </h3>
                <p class="text-gray-700 mb-4">
                    You are successfully authenticated with Google! Calendar features will be available here.
                </p>
                <div id="calendar-data" class="bg-white p-4 rounded-lg mb-4">
                    <div class="flex items-center justify-center text-blue-600 py-4">
                        <svg class="animate-spin h-8 w-8 mr-3" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <div>
                            <p class="font-semibold text-lg">Loading Calendar Data...</p>
                            <p class="text-sm text-gray-600">Fetching your calendars and events</p>
                        </div>
                    </div>
                </div>
                <button
                    id="google-signout-button"
                    class="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center"
                >
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                    </svg>
                    Sign Out
                </button>
                <p class="text-xs text-gray-500 mt-3 text-center">
                    Signing out will remove your access token from this browser
                </p>
            `;

      // Add sign-out handler
      setTimeout(() => {
        const signOutButton = document.getElementById("google-signout-button");
        if (signOutButton) {
          signOutButton.addEventListener("click", function () {
            console.log("Sign-Out button clicked");
            CookieManager.deleteCookie("google_oauth_access_token");
            console.log("Access token removed from cookies");
            window.location.reload();
          });
        }
      }, 100);

      // Load calendar data
      setTimeout(async () => {
        const calendarDataDiv = document.getElementById("calendar-data");
        if (!calendarDataDiv) return;

        try {
          console.log("Fetching calendars...");
          const calendars = await CalendarManager.listCalendars();
          console.log(`Found ${calendars.length} calendars`);

          // Try to find SFLT calendar
          const sfltCalendar = calendars.find((cal) => cal.summary === "SFLT");

          let html = '<div class="space-y-4">';

          // If SFLT calendar found, show events
          if (sfltCalendar) {
            console.log("SFLT calendar found, fetching events...");

            const [allPastEvents, allUpcomingEvents] = await Promise.all([
              CalendarManager.getRecentPastEvents(sfltCalendar.id, 20),
              CalendarManager.getUpcomingEvents(sfltCalendar.id, 10),
            ]);

            // Filter events to only show those with title "B-SFLT-D1 💃"
            const pastEvents = allPastEvents.filter((event) => event.summary === "B-SFLT-D1 💃").slice(0, 5);
            const upcomingEvents = allUpcomingEvents.filter((event) => event.summary === "B-SFLT-D1 💃").slice(0, 3);

            console.log(`Past events: ${pastEvents.length}, Upcoming events: ${upcomingEvents.length}`);

            // Upcoming events
            html += "<div>";
            html += '<h4 class="font-semibold text-gray-800 mb-3">🔜 Upcoming Events</h4>';
            if (upcomingEvents.length > 0) {
              html += '<div class="space-y-2">';
              upcomingEvents.forEach((event, index) => {
                // For first upcoming event, use most recent past event as previous
                // For subsequent events, use previous upcoming event
                const previousEvent =
                  index === 0 ? (pastEvents.length > 0 ? pastEvents[0] : null) : upcomingEvents[index - 1];
                html += CalendarManager.formatEvent(event, previousEvent);
              });
              html += "</div>";
            } else {
              html += '<p class="text-sm text-gray-500 italic">No upcoming events</p>';
            }
            html += "</div>";

            // Recent past events
            html += '<div class="border-t pt-4 mt-4">';
            html += '<h4 class="font-semibold text-gray-800 mb-3">📜 Recent Past Events</h4>';
            if (pastEvents.length > 0) {
              html += '<div class="space-y-2">';
              pastEvents.forEach((event, index) => {
                // For past events (most recent first), previous is the one after in array (earlier chronologically)
                const previousEvent = index < pastEvents.length - 1 ? pastEvents[index + 1] : null;
                html += CalendarManager.formatEvent(event, previousEvent);
              });
              html += "</div>";
            } else {
              html += '<p class="text-sm text-gray-500 italic">No recent past events</p>';
            }
            html += "</div>";
          } else {
            html += '<div class="text-center py-8">';
            html +=
              '<p class="text-gray-600">No "SFLT" calendar found. Please create an "SFLT" calendar to see events.</p>';
            html += "</div>";
          }

          html += "</div>";
          calendarDataDiv.innerHTML = html;
        } catch (error) {
          console.error("Failed to load calendar data:", error);
          calendarDataDiv.innerHTML = `
            <div class="flex items-center justify-center text-red-600 py-4">
              <svg class="w-12 h-12 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <div>
                <p class="font-semibold text-lg">Failed to Load Calendar Data</p>
                <p class="text-sm text-gray-600">${error.message}</p>
              </div>
            </div>
          `;
        }
      }, 500);
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

      // Add click handler for sign-in button to initiate OAuth flow
      setTimeout(() => {
        const signInButton = document.getElementById("google-signin-button");
        if (signInButton) {
          signInButton.addEventListener("click", async function () {
            console.log("Google Sign-In button clicked (Lambda@Edge pattern)");

            // Initiate OAuth PKCE flow
            // Lambda@Edge will handle the callback and token exchange
            try {
              await OAuthManager.initiateOAuthFlow();
            } catch (error) {
              console.error("OAuth flow initiation failed:", error);
              alert(`OAuth Error: ${error.message}`);
            }
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
