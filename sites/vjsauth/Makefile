PORT_NUMBER ?= 5173
THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
THIS_DIR_NAME := $(notdir $(patsubst %/,%,$(THIS_DIR)))
TEST_DIR := tests/$(THIS_DIR_NAME)

.PHONY: debug serve serve-legacy serve-oauth serve-all build docs format test clean

debug:
	@echo "THIS_DIR: $(THIS_DIR)"
	@echo "THIS_DIR_NAME: $(THIS_DIR_NAME)"
	@echo "PORT_NUMBER: $(PORT_NUMBER)"
	@echo "TEST_DIR: $(TEST_DIR)"

serve:
	@echo "Starting unified development server on port $(PORT_NUMBER)..."
	@echo ""
	@echo "This server provides:"
	@echo "  - Static file serving (like CloudFront + S3)"
	@echo "  - OAuth callback handler (like Lambda@Edge)"
	@echo ""
	@echo "Make sure environment variables are set:"
	@echo "  GOOGLE_OAUTH_CLIENT_ID"
	@echo "  GOOGLE_OAUTH_CLIENT_SECRET"
	@echo "  FRONTEND_URL (optional, defaults to http://localhost:5173)"
	@echo ""
	PORT=$(PORT_NUMBER) uv run python $(THIS_DIR)/server.py



build:
	@echo "No build step required for vjsauth"

docs:
	# Markdown
	uvx --from md-toc md_toc --in-place github --header-levels 4 *.md
	uvx rumdl check --fix --config ../../pyproject.toml *.md

format:
	# Code Formatting
	npx -y prettier './**/*.{js,css,html}' --write --print-width 120

test: format
	uv run pytest ../../"$(TEST_DIR)" --base-url http://localhost:$(PORT_NUMBER) --browser chromium

clean:
	@echo "Cleaning temporary files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@echo "Clean complete"
