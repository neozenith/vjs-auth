"""
Development Server for VJS Auth - Lambda@Edge Wrapper

This server provides:
1. Static file serving (simulating S3 + CloudFront)
2. Lambda@Edge handler wrapper for local testing

Production architecture:
- CloudFront serves static files from S3
- Lambda@Edge (handler.py) intercepts /oauth/callback for token exchange

Local development:
- Flask serves static files
- Flask wraps handler.py to simulate Lambda@Edge environment
"""

import os
from pathlib import Path
from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import urllib.parse

# Import the Lambda@Edge handler
from handler import lambda_handler

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

# Port configuration
PORT = int(os.environ.get("PORT", "5173"))
FRONTEND_URL = f"http://localhost:{PORT}"


def flask_request_to_lambda_event(flask_request):
    """
    Convert Flask request to Lambda@Edge origin-request event format.

    CloudFront Lambda@Edge event structure for origin-request:
    {
        'Records': [{
            'cf': {
                'request': {
                    'uri': '/oauth/callback',
                    'querystring': 'code=xxx&state=yyy',
                    'headers': {
                        'host': [{'key': 'Host', 'value': 'example.com'}],
                        ...
                    },
                    'method': 'GET'
                }
            }
        }]
    }
    """
    # Convert Flask headers to CloudFront headers format
    cf_headers = {}
    for header_name, header_value in flask_request.headers:
        header_key = header_name.lower()
        cf_headers[header_key] = [
            {"key": header_name, "value": header_value}
        ]

    # Add custom headers for OAuth configuration (DEVELOPMENT ONLY)
    # Production uses AWS Secrets Manager instead of headers
    # These headers allow handler.py to work locally without Secrets Manager
    cf_headers["x-oauth-client-id"] = [
        {"key": "X-OAuth-Client-Id", "value": GOOGLE_CLIENT_ID}
    ]
    cf_headers["x-oauth-client-secret"] = [
        {"key": "X-OAuth-Client-Secret", "value": GOOGLE_CLIENT_SECRET}
    ]
    cf_headers["x-oauth-frontend-url"] = [
        {"key": "X-OAuth-Frontend-URL", "value": FRONTEND_URL}
    ]

    # Build Lambda@Edge event
    event = {
        "Records": [
            {
                "cf": {
                    "request": {
                        "uri": flask_request.path,
                        "querystring": flask_request.query_string.decode("utf-8"),
                        "headers": cf_headers,
                        "method": flask_request.method,
                    }
                }
            }
        ]
    }

    return event


def lambda_response_to_flask(lambda_response):
    """
    Convert Lambda@Edge response to Flask response.

    Lambda@Edge response format:
    {
        'status': '302',
        'statusDescription': 'Found',
        'headers': {
            'location': [{'key': 'Location', 'value': 'https://...'}],
            'set-cookie': [{'key': 'Set-Cookie', 'value': '...'}],
            ...
        }
    }
    """
    status_code = int(lambda_response.get("status", 200))

    # Create Flask response
    # For redirects, we need to extract the location
    headers_dict = lambda_response.get("headers", {})

    location = None
    if "location" in headers_dict:
        location = headers_dict["location"][0]["value"]

    # Create response
    if location:
        response = make_response("", status_code)
        response.headers["Location"] = location
    else:
        response = make_response("", status_code)

    # Add all headers
    for header_name, header_list in headers_dict.items():
        if header_name == "location":
            continue  # Already handled

        for header_item in header_list:
            header_key = header_item["key"]
            header_value = header_item["value"]

            # Special handling for Set-Cookie (can have multiple)
            if header_name == "set-cookie":
                response.headers.add(header_key, header_value)
            else:
                response.headers[header_key] = header_value

    return response


@app.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    """
    Flask wrapper for Lambda@Edge OAuth callback handler.

    Converts Flask request to Lambda@Edge event format,
    calls handler.py, then converts Lambda@Edge response to Flask response.

    In production, CloudFront would call handler.lambda_handler directly.
    """
    try:
        # Convert Flask request to Lambda@Edge event format
        event = flask_request_to_lambda_event(request)

        # Call Lambda@Edge handler
        lambda_response = lambda_handler(event, None)

        # Convert Lambda@Edge response to Flask response
        return lambda_response_to_flask(lambda_response)

    except Exception as e:
        app.logger.error(f"OAuth callback wrapper error: {str(e)}")
        return make_response(f"Internal Error: {str(e)}", 500)




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
