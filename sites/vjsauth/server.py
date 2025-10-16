"""
Unified Development Server for VJS Auth.

This server provides both:
1. Static file serving (simulating S3 + CloudFront)
2. OAuth callback handling (simulating Lambda@Edge)

This mimics the production architecture where:
- CloudFront serves static files from S3
- Lambda@Edge intercepts /oauth/callback for token exchange

Everything runs on the same host:port for simplified local development.
"""

import os
from pathlib import Path
from flask import Flask, request, jsonify, redirect, make_response, send_from_directory
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Directory containing static files
SCRIPT_DIR = Path(__file__).parent.resolve()

# Create Flask app with static file handling disabled (we'll do it manually)
app = Flask(__name__, static_folder=None)
CORS(app)  # Enable CORS for local development

# OAuth Configuration
# IMPORTANT: Set these as environment variables for production
GOOGLE_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

# Port configuration
PORT = int(os.environ.get("PORT", "5173"))
FRONTEND_URL = f"http://localhost:{PORT}"


@app.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    """
    Lambda@Edge-style OAuth callback handler.

    This simulates what Lambda@Edge would do in production:
    1. Intercepts OAuth callback from Google
    2. Extracts authorization code and state
    3. Retrieves PKCE code_verifier from query params (passed via state)
    4. Exchanges code for access token with Google
    5. Sets cookie with access token
    6. Redirects back to frontend

    In production, this would be a Lambda@Edge function at CloudFront.
    """
    try:
        # Get OAuth callback parameters
        code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")

        # Handle OAuth errors
        if error:
            error_description = request.args.get("error_description", "Unknown error")
            app.logger.error(f"OAuth error: {error} - {error_description}")
            # Redirect to frontend with error
            return redirect(f"{FRONTEND_URL}/?oauth_error={error}")

        if not code:
            app.logger.error("No authorization code received")
            return redirect(f"{FRONTEND_URL}/?oauth_error=no_code")

        if not state:
            app.logger.error("No state parameter received")
            return redirect(f"{FRONTEND_URL}/?oauth_error=no_state")

        # Decode state parameter to extract code_verifier
        # State format: base64(JSON({csrf: xxx, verifier: xxx}))
        try:
            import base64
            import json

            state_json = base64.b64decode(state).decode("utf-8")
            state_data = json.loads(state_json)
            code_verifier = state_data.get("verifier")
            csrf_token = state_data.get("csrf")

            if not code_verifier:
                app.logger.error("No code_verifier in state parameter")
                return redirect(f"{FRONTEND_URL}/?oauth_error=no_verifier")

            app.logger.info("Successfully extracted code_verifier from state parameter")

        except Exception as decode_error:
            app.logger.error(f"Failed to decode state parameter: {decode_error}")
            return redirect(f"{FRONTEND_URL}/?oauth_error=invalid_state")

        # Build redirect URI (must match what was sent to Google)
        redirect_uri = f"{request.host_url}oauth/callback"

        # Exchange authorization code for access token
        token_params = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        response = requests.post(
            GOOGLE_TOKEN_ENDPOINT,
            data=token_params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if not response.ok:
            error_data = response.json()
            error_msg = error_data.get("error", "token_exchange_failed")
            app.logger.error(f"Token exchange failed: {error_msg}")
            return redirect(f"{FRONTEND_URL}/?oauth_error={error_msg}")

        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            app.logger.error("No access token in response")
            return redirect(f"{FRONTEND_URL}/?oauth_error=no_token")

        # Create redirect response to frontend
        response = make_response(redirect(FRONTEND_URL))

        # Set cookie with access token (Lambda@Edge would do this)
        # Using SameSite=Lax for security (same as frontend)
        response.set_cookie(
            "google_oauth_access_token",
            access_token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=False,  # Allow JavaScript access (needed for frontend)
            secure=False,  # Set to True in production with HTTPS
            samesite="Lax",
            path="/",
        )

        app.logger.info("OAuth flow completed successfully, redirecting to frontend")
        return response

    except Exception as e:
        app.logger.error(f"OAuth callback error: {str(e)}")
        return redirect(f"{FRONTEND_URL}/?oauth_error=internal_error")


@app.route("/oauth/token", methods=["POST"])
def exchange_token():
    """
    Exchange authorization code for access token.

    Expected JSON body:
    {
        "code": "authorization_code",
        "code_verifier": "pkce_verifier",
        "redirect_uri": "http://localhost:5173"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid request body"}), 400

        code = data.get("code")
        code_verifier = data.get("code_verifier")
        redirect_uri = data.get("redirect_uri")

        if not all([code, code_verifier, redirect_uri]):
            return jsonify(
                {
                    "error": "Missing required fields",
                    "required": ["code", "code_verifier", "redirect_uri"],
                }
            ), 400

        # Exchange code for token with Google
        token_params = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        response = requests.post(
            GOOGLE_TOKEN_ENDPOINT,
            data=token_params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if not response.ok:
            error_data = response.json()
            return jsonify(
                {
                    "error": error_data.get("error", "token_exchange_failed"),
                    "error_description": error_data.get(
                        "error_description", "Failed to exchange token"
                    ),
                }
            ), response.status_code

        # Return the token data to frontend
        token_data = response.json()
        return jsonify(token_data), 200

    except Exception as e:
        app.logger.error(f"Token exchange error: {str(e)}")
        return jsonify({"error": "internal_server_error", "message": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "ok",
            "client_id_configured": bool(GOOGLE_CLIENT_ID),
            "client_secret_configured": bool(GOOGLE_CLIENT_SECRET),
        }
    ), 200


# =============================================================================
# Static File Serving (Simulates CloudFront + S3)
# =============================================================================


@app.route("/")
def serve_index():
    """Serve index.html for the root path."""
    return send_from_directory(SCRIPT_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    """
    Serve static files from SCRIPT_DIR.

    This simulates CloudFront serving static content from S3.
    In production, CloudFront would serve these files directly,
    and Lambda@Edge would only intercept /oauth/callback.
    """
    try:
        return send_from_directory(SCRIPT_DIR, path)
    except FileNotFoundError:
        # If file not found, return index.html for client-side routing
        return send_from_directory(SCRIPT_DIR, "index.html")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("VJS Auth Unified Development Server")
    print("=" * 70)
    print(f"Server starting on http://localhost:{PORT}")
    print()
    print("Features:")
    print("  ✓ Static file serving (simulates CloudFront + S3)")
    print("  ✓ OAuth callback handler (simulates Lambda@Edge)")
    print()
    print("Configuration:")
    print(f"  Client ID: {GOOGLE_CLIENT_ID}")
    print(
        f"  Client Secret: {'✓ Configured' if GOOGLE_CLIENT_SECRET else '✗ Not configured'}"
    )
    print(f"  Static files: {SCRIPT_DIR}")
    print()
    print("Endpoints:")
    print(f"  http://localhost:{PORT}/              → Static site (index.html)")
    print(f"  http://localhost:{PORT}/oauth/callback → OAuth token exchange")
    print(f"  http://localhost:{PORT}/health         → Health check")
    print("=" * 70 + "\n")

    app.run(host="127.0.0.1", port=PORT, debug=True)
