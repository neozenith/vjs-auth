THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
THIS_DIR_NAME := $(notdir $(patsubst %/,%,$(THIS_DIR)))

# AWS Profile from config
AWS_PROFILE := sflt

# Auto-detect git branch for config selection
GIT_BRANCH := $(shell git branch --show-current)
CONFIG_FILE := config/app-config-$(GIT_BRANCH).json

.PHONY: debug init synth diff deploy destroy list clean bootstrap

debug:
	@echo "THIS_DIR: $(THIS_DIR)"
	@echo "THIS_DIR_NAME: $(THIS_DIR_NAME)"
	@echo "AWS_PROFILE: $(AWS_PROFILE)"
	@echo "GIT_BRANCH: $(GIT_BRANCH)"
	@echo "CONFIG_FILE: $(CONFIG_FILE)"

init:
	@echo "Installing CDK dependencies..."
	python3 -m venv .venv || true
	. .venv/bin/activate && pip install -r requirements.txt

bootstrap:
	@echo "Bootstrapping CDK in AWS account..."
	@echo "Using profile: $(AWS_PROFILE)"
	. .venv/bin/activate && AWS_PROFILE=$(AWS_PROFILE) cdk bootstrap

synth:
	@echo "Synthesizing CloudFormation templates..."
	@echo "Using config: $(CONFIG_FILE)"
	@echo "Git branch: $(GIT_BRANCH)"
	. .venv/bin/activate && APP_CONFIG=$(CONFIG_FILE) AWS_PROFILE=$(AWS_PROFILE) cdk synth

diff:
	@echo "Showing differences between deployed and local stacks..."
	@echo "Using config: $(CONFIG_FILE)"
	. .venv/bin/activate && APP_CONFIG=$(CONFIG_FILE) AWS_PROFILE=$(AWS_PROFILE) cdk diff

deploy:
	@echo "Deploying CDK stacks..."
	@echo "Using config: $(CONFIG_FILE)"
	@echo "Git branch: $(GIT_BRANCH)"
	@echo "AWS Profile: $(AWS_PROFILE)"
	. .venv/bin/activate && APP_CONFIG=$(CONFIG_FILE) AWS_PROFILE=$(AWS_PROFILE) cdk deploy --all --require-approval never

destroy:
	@echo "Destroying CDK stacks..."
	@echo "Using config: $(CONFIG_FILE)"
	@echo "WARNING: This will delete all resources!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		. .venv/bin/activate && APP_CONFIG=$(CONFIG_FILE) AWS_PROFILE=$(AWS_PROFILE) cdk destroy --all --force; \
	fi

list:
	@echo "Listing all stacks..."
	. .venv/bin/activate && APP_CONFIG=$(CONFIG_FILE) AWS_PROFILE=$(AWS_PROFILE) cdk list

clean:
	@echo "Cleaning CDK artifacts..."
	rm -rf cdk.out
	rm -rf .venv
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Clean complete"
