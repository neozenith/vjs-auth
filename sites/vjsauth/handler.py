"""
Lambda@Edge OAuth Callback Handler

This is the production Lambda@Edge function that handles OAuth callbacks.
It's designed to work within Lambda@Edge constraints:
- Max 5 second execution time
- Max 1MB response size
- Origin-request event type (can make network calls)
- No environment variables (config must be retrieved at runtime)

Production Setup:
1. Store OAuth secrets in AWS Secrets Manager or Systems Manager Parameter Store
2. Lambda@Edge IAM role needs secretsmanager:GetSecretValue and kms:Decrypt permissions
3. Deploy this as Lambda@Edge function in us-east-1
4. Attach to CloudFront distribution as origin-request trigger
5. Configure for path pattern: /oauth/callback
6. Replace get_config_from_headers() with get_oauth_config_from_secrets_manager()

Secrets Management:
- Production: Retrieves secrets from AWS Secrets Manager at runtime with caching
- Development: server.py injects secrets as custom headers for local testing only

Local Testing:
Use server.py which wraps this handler in Flask for development.
"""

import json
import base64
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional

# =============================================================================
# Configuration Constants
# =============================================================================

# Local development defaults (production uses AWS Secrets Manager)
DEFAULT_HOST = "localhost:5173"
DEFAULT_FRONTEND_URL = "http://localhost:5173"
OAUTH_CALLBACK_PATH = "/oauth/callback"

# OAuth endpoints
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
TOKEN_EXCHANGE_TIMEOUT = 4  # seconds (within 5s Lambda@Edge limit)

# Cookie configuration
COOKIE_NAME = "google_oauth_access_token"
COOKIE_MAX_AGE = 7 * 24 * 60 * 60  # 7 days


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """
    Lambda@Edge handler for OAuth callback.

    Event structure for origin-request:
    {
        'Records': [{
            'cf': {
                'request': {
                    'uri': '/oauth/callback',
                    'querystring': 'code=xxx&state=yyy',
                    'headers': {...},
                    'method': 'GET'
                }
            }
        }]
    }

    Returns CloudFront response object with redirect and cookie.
    """
    try:
        request = event["Records"][0]["cf"]["request"]
        querystring = request.get("querystring", "")

        # Parse query parameters
        params = parse_query_string(querystring)
        code = params.get("code")
        state = params.get("state")
        error = params.get("error")

        # Get configuration (development: from headers, production: use Secrets Manager)
        headers = request.get("headers", {})
        config = get_config_from_headers(headers)  # TODO: Replace with get_oauth_config_from_secrets_manager() for production

        # Handle OAuth errors
        if error:
            error_description = params.get("error_description", "Unknown error")
            print(f"OAuth error: {error} - {error_description}")
            return create_redirect_response(
                config["frontend_url"], {"oauth_error": error}
            )

        if not code:
            print("No authorization code received")
            return create_redirect_response(
                config["frontend_url"], {"oauth_error": "no_code"}
            )

        if not state:
            print("No state parameter received")
            return create_redirect_response(
                config["frontend_url"], {"oauth_error": "no_state"}
            )

        # Decode state parameter to extract code_verifier
        try:
            state_json = base64.b64decode(state).decode("utf-8")
            state_data = json.loads(state_json)
            code_verifier = state_data.get("verifier")

            if not code_verifier:
                print("No code_verifier in state parameter")
                return create_redirect_response(
                    config["frontend_url"], {"oauth_error": "no_verifier"}
                )

            print("Successfully extracted code_verifier from state parameter")

        except Exception as decode_error:
            print(f"Failed to decode state parameter: {decode_error}")
            return create_redirect_response(
                config["frontend_url"], {"oauth_error": "invalid_state"}
            )

        # Build redirect URI (must match what was sent to Google)
        # Extract host from request headers
        host = get_header_value(headers, "host", DEFAULT_HOST)

        # Determine protocol - use http for localhost, https for production
        protocol = "http" if "localhost" in host or "127.0.0.1" in host else "https"
        redirect_uri = f"{protocol}://{host}{OAUTH_CALLBACK_PATH}"

        # Exchange authorization code for access token
        token_response = exchange_token(
            code=code,
            code_verifier=code_verifier,
            redirect_uri=redirect_uri,
            client_id=config["client_id"],
            client_secret=config["client_secret"],
        )

        if "error" in token_response:
            error_msg = token_response.get("error", "token_exchange_failed")
            print(f"Token exchange failed: {error_msg}")
            return create_redirect_response(
                config["frontend_url"], {"oauth_error": error_msg}
            )

        access_token = token_response.get("access_token")
        if not access_token:
            print("No access token in response")
            return create_redirect_response(
                config["frontend_url"], {"oauth_error": "no_token"}
            )

        # Create redirect response with cookie
        print("OAuth flow completed successfully")
        return create_redirect_response(
            config["frontend_url"],
            params=None,
            cookie_name=COOKIE_NAME,
            cookie_value=access_token,
            cookie_max_age=COOKIE_MAX_AGE,
        )

    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        # Try to get frontend URL from config or use default
        frontend_url = DEFAULT_FRONTEND_URL
        try:
            headers = event["Records"][0]["cf"]["request"].get("headers", {})
            config = get_config_from_headers(headers)
            frontend_url = config["frontend_url"]
        except (KeyError, IndexError, TypeError):
            pass

        return create_redirect_response(
            frontend_url, {"oauth_error": "internal_error"}
        )


def parse_query_string(querystring: str) -> Dict[str, str]:
    """Parse URL query string into dictionary."""
    params = {}
    if querystring:
        for param in querystring.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[urllib.parse.unquote(key)] = urllib.parse.unquote(value)
    return params


def get_header_value(
    headers: Dict[str, list], header_name: str, default: str = ""
) -> str:
    """
    Get header value from CloudFront headers dict.

    CloudFront headers format: {'header-name': [{'key': 'Header-Name', 'value': 'value'}]}
    """
    header_list = headers.get(header_name.lower(), [])
    if header_list and len(header_list) > 0:
        return header_list[0].get("value", default)
    return default


def get_config_from_headers(headers: Dict[str, list]) -> Dict[str, str]:
    """
    Extract configuration from request headers (DEVELOPMENT ONLY).

    This function is used for local development where server.py injects
    OAuth secrets as custom headers. In production, this should be replaced
    with get_oauth_config_from_secrets_manager() which retrieves secrets
    from AWS Secrets Manager.

    Expected headers (injected by server.py in development):
    - X-OAuth-Client-Id: Google OAuth client ID
    - X-OAuth-Client-Secret: Google OAuth client secret
    - X-OAuth-Frontend-URL: Frontend URL for redirects
    """
    return {
        "client_id": get_header_value(headers, "x-oauth-client-id", ""),
        "client_secret": get_header_value(headers, "x-oauth-client-secret", ""),
        "frontend_url": get_header_value(headers, "x-oauth-frontend-url", DEFAULT_FRONTEND_URL),
    }


def exchange_token(
    code: str,
    code_verifier: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> Dict[str, Any]:
    """
    Exchange authorization code for access token with Google.

    Uses urllib (no external dependencies allowed in Lambda@Edge).
    """
    # Build POST data
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }

    # Encode data
    encoded_data = urllib.parse.urlencode(data).encode("utf-8")

    # Create request
    req = urllib.request.Request(
        GOOGLE_TOKEN_ENDPOINT,
        data=encoded_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        # Make request (within 5 second Lambda@Edge timeout)
        with urllib.request.urlopen(req, timeout=TOKEN_EXCHANGE_TIMEOUT) as response:
            response_data = response.read().decode("utf-8")
            return json.loads(response_data)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            error_data = json.loads(error_body)
            return {"error": error_data.get("error", "token_exchange_failed")}
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"error": "token_exchange_failed"}
    except Exception as e:
        print(f"Token exchange exception: {str(e)}")
        return {"error": "network_error"}


def create_redirect_response(
    location: str,
    params: Optional[Dict[str, str]] = None,
    cookie_name: Optional[str] = None,
    cookie_value: Optional[str] = None,
    cookie_max_age: int = COOKIE_MAX_AGE,
) -> Dict[str, Any]:
    """
    Create CloudFront redirect response with optional cookie.

    Returns Lambda@Edge response object.
    """
    # Build location URL with query params
    if params:
        query_string = urllib.parse.urlencode(params)
        location = f"{location}?{query_string}"

    # Build response headers
    headers = {
        "location": [{"key": "Location", "value": location}],
        "cache-control": [{"key": "Cache-Control", "value": "no-cache, no-store, must-revalidate"}],
    }

    # Add cookie if provided
    if cookie_name and cookie_value:
        # Build cookie string
        cookie_parts = [
            f"{cookie_name}={cookie_value}",
            f"Max-Age={cookie_max_age}",
            "Path=/",
            "SameSite=Lax",
            # Note: Secure flag should be True in production with HTTPS
            # "Secure",  # Uncomment for production
        ]
        cookie_string = "; ".join(cookie_parts)

        headers["set-cookie"] = [{"key": "Set-Cookie", "value": cookie_string}]

    return {
        "status": "302",
        "statusDescription": "Found",
        "headers": headers,
    }


# =============================================================================
# Production Secrets Management (AWS Secrets Manager)
# =============================================================================
# Uncomment and use this function for production deployments.
# Replace get_config_from_headers() call in lambda_handler() with this.
#
# Requirements:
# 1. Create secret in AWS Secrets Manager (must be in us-east-1 for Lambda@Edge):
#    aws secretsmanager create-secret \
#      --name oauth-config \
#      --region us-east-1 \
#      --secret-string '{
#        "client_id": "YOUR_GOOGLE_CLIENT_ID",
#        "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",
#        "frontend_url": "https://yourdomain.com"
#      }'
#
# 2. Add IAM permissions to Lambda@Edge execution role:
#    {
#      "Effect": "Allow",
#      "Action": [
#        "secretsmanager:GetSecretValue",
#        "kms:Decrypt"
#      ],
#      "Resource": [
#        "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:oauth-config-*",
#        "arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID"
#      ]
#    }
#
# 3. Uncomment this function and boto3 import at top of file:
#    import boto3
#
# # Global cache for secrets (reused across Lambda invocations)
# _cached_oauth_config = None
# _secrets_client = None
#
# def get_oauth_config_from_secrets_manager() -> Dict[str, str]:
#     """
#     Retrieve OAuth configuration from AWS Secrets Manager with caching.
#
#     Caches the secret value in memory to reduce API calls and improve performance.
#     The cache persists across Lambda invocations in the same execution environment.
#     """
#     global _cached_oauth_config, _secrets_client
#
#     # Return cached config if available
#     if _cached_oauth_config is not None:
#         return _cached_oauth_config
#
#     # Initialize Secrets Manager client (reused across invocations)
#     if _secrets_client is None:
#         _secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
#
#     # Retrieve and cache the secret
#     try:
#         response = _secrets_client.get_secret_value(SecretId='oauth-config')
#         secret_string = response['SecretString']
#         _cached_oauth_config = json.loads(secret_string)
#         print("Successfully retrieved OAuth config from Secrets Manager")
#         return _cached_oauth_config
#     except Exception as e:
#         print(f"Failed to retrieve secret from Secrets Manager: {str(e)}")
#         # Fallback to default values (or raise exception for production)
#         return {
#             "client_id": "",
#             "client_secret": "",
#             "frontend_url": DEFAULT_FRONTEND_URL,
#         }
