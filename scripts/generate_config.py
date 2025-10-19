#!/usr/bin/env python3
"""
Generate config.json from Jinja2 template using environment variables.

This script loads environment variables from .env file and templates
the config.example.json.jinja2 file to create config.json.

Usage:
    python scripts/generate_config.py

Requirements:
    - python-dotenv
    - jinja2
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

load_dotenv()

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

def generate_config():
    """Generate config.json from template using environment variables."""

    # Get required environment variables
    google_oauth_client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    if not google_oauth_client_id:
        print(
            "Error: GOOGLE_OAUTH_CLIENT_ID not found in environment variables .env or exported to the environemnt",
            file=sys.stderr,
        )
        sys.exit(1)

    # Extract the numeric part (remove .apps.googleusercontent.com if present)
    if ".apps.googleusercontent.com" in google_oauth_client_id:
        google_oauth_client_id = google_oauth_client_id.split(".apps.googleusercontent.com")[0]

    print(f"✓ Found GOOGLE_OAUTH_CLIENT_ID: {google_oauth_client_id}")

    # Setup Jinja2 environment
    template_dir = PROJECT_ROOT / "sites" / "vjsauth"
    template_name = "config.example.json.jinja2"
    output_path = template_dir / "config.json"

    

    # Render template with environment variables
    rendered = (Environment(loader=FileSystemLoader(template_dir))
                .get_template(template_name)
                .render(GOOGLE_OAUTH_CLIENT_ID=google_oauth_client_id,))

    # Write rendered config to output file
    output_path.write_text(rendered)
    print(f"✓ Generated config file: {output_path}")


if __name__ == "__main__":
    generate_config()
    
