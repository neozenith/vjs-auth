init:
	uv sync
	uv run playwright install

config: sites/vjsauth/config.json
sites/vjsauth/config.json: sites/vjsauth/config.example.json.jinja2 .env
	uv run python scripts/generate_config.py

serve: sites/vjsauth/config.json
	make -C sites/vjsauth serve
