#!/usr/bin/env python3
"""CDK app entry point."""

import os
import aws_cdk as cdk
from lib.app_context import AppContext
from stacks.storage_stack import StorageStack


# Initialize app and load configuration
app = cdk.App()

# Get config path from context or environment variable
config_path = app.node.try_get_context("APP_CONFIG") or os.getenv("APP_CONFIG")
app_context = AppContext(config_path)

# Define environment from config
env = cdk.Environment(
    account=app_context.account,
    region=app_context.region,
)

# Create stacks
storage_stack = StorageStack(
    app,
    app_context.get_stack_name("Storage"),
    app_context=app_context,
    env=env,
)

app.synth()
