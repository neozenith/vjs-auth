init:
	uv sync
	uv run playwright install

serve:
	make -C sites/vjsauth serve
