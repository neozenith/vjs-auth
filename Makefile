init:
	uv sync
	uv run playwright install
	make -C infra init

config: sites/vjsauth/config.json
sites/vjsauth/config.json: sites/vjsauth/config.example.json.jinja2 .env
	uv run python scripts/generate_config.py

serve: sites/vjsauth/config.json
	make -C sites/vjsauth serve

# Infrastructure commands
infra-synth:
	make -C infra synth

infra-diff:
	make -C infra diff

infra-deploy:
	make -C infra deploy

infra-destroy:
	make -C infra destroy

infra-list:
	make -C infra list

infra-bootstrap:
	make -C infra bootstrap
