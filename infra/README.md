# Infrastructure Setup

CDK-based infrastructure automation for vjs-auth project.

## Overview

This directory contains AWS CDK infrastructure code following the [AWS CDK DevOps template best practices](https://github.com/aws-samples/aws-cdk-project-template-for-devops).

## Directory Structure

```
infra/
├── app.py                 # CDK app entry point
├── cdk.json              # CDK configuration
├── Makefile              # Infrastructure automation tasks
├── config/               # Environment-specific configurations
│   └── app-config-main.json
├── lib/                  # Shared libraries and utilities
│   └── app_context.py   # Configuration management
└── stacks/              # CDK stack definitions
    └── storage_stack.py # S3 bucket stack
```

## Configuration

The infrastructure uses branch-based configuration files in `config/app-config-{branch}.json`.

**Example configuration (`config/app-config-main.json`):**

```json
{
    "Project": {
        "Name": "VjsAuth",
        "Stage": "main",
        "Account": "",
        "Region": "us-east-1",
        "Profile": "sflt"
    },
    "Stack": {
        "Storage": {
            "Name": "StorageStack",
            "BucketName": "vjsauth"
        }
    }
}
```

### Branch-Based Namespacing

The system automatically uses the current git branch to:
1. Select the appropriate config file (`app-config-{branch}.json`)
2. Namespace all resources with the branch name
3. Allow parallel deployments of different branches

**Example:** On the `main` branch, the S3 bucket will be named `vjsauth-main`.

## AWS Profile

The infrastructure uses the AWS profile `sflt` as configured in `config/app-config-main.json`.

Ensure this profile is configured in your `~/.aws/credentials`:

```
[sflt]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

## Quick Start

### 1. Initialize (First Time Only)

```bash
cd infra
make init
```

This creates a Python virtual environment and installs CDK dependencies.

### 2. Bootstrap CDK (First Time Per Account/Region)

```bash
make bootstrap
```

This sets up CDK resources in your AWS account.

### 3. Synthesize CloudFormation Templates

```bash
make synth
```

### 4. Deploy Infrastructure

```bash
make deploy
```

## Available Make Commands

### Infrastructure Operations

- `make init` - Initialize Python virtual environment and install dependencies
- `make bootstrap` - Bootstrap CDK in AWS account (first time only)
- `make synth` - Synthesize CloudFormation templates
- `make diff` - Show differences between deployed and local stacks
- `make deploy` - Deploy all stacks to AWS
- `make destroy` - Destroy all stacks (with confirmation)
- `make list` - List all stacks
- `make clean` - Clean CDK artifacts and virtual environment

### From Root Directory

You can also run these commands from the project root:

```bash
make infra-synth
make infra-deploy
make infra-destroy
make infra-list
make infra-bootstrap
```

## Current Stacks

### StorageStack

**Purpose:** S3 bucket for static website hosting and storage.

**Resources:**
- S3 Bucket with branch-based naming: `{BucketName}-{branch}`
- Versioning enabled
- Server-side encryption (AES256)
- Public access blocked by default
- Auto-delete on stack destruction (for development)

**Configuration:**
```json
"Storage": {
    "Name": "StorageStack",
    "BucketName": "vjsauth"
}
```

## Development Workflow

### Working on a Feature Branch

1. Create a new git branch:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Create a corresponding config file:
   ```bash
   cp config/app-config-main.json config/app-config-feature-my-feature.json
   ```

3. Update the `Stage` in the new config:
   ```json
   {
       "Project": {
           "Stage": "feature-my-feature",
           ...
       }
   }
   ```

4. Deploy to your feature environment:
   ```bash
   make deploy
   ```

This creates a completely separate set of resources namespaced with your branch name.

### Cleanup

When done with a feature branch:

```bash
make destroy
```

This removes all AWS resources created by CDK for that branch.

## Fully Destructible Deployment

All resources are configured for easy teardown:

- **RemovalPolicy:** `DESTROY`
- **AutoDeleteObjects:** Enabled for S3 buckets
- All resources include proper cleanup automation

**Warning:** This is appropriate for development. For production deployments, change `RemovalPolicy` to `RETAIN` in stack definitions.

## Adding New Stacks

1. Create a new stack file in `stacks/`:
   ```python
   # stacks/my_new_stack.py
   from aws_cdk import Stack
   from constructs import Construct

   class MyNewStack(Stack):
       def __init__(self, scope, construct_id, app_context, **kwargs):
           super().__init__(scope, construct_id, **kwargs)
           # Add resources here
   ```

2. Add configuration in `config/app-config-*.json`:
   ```json
   "Stack": {
       "MyNew": {
           "Name": "MyNewStack",
           ...
       }
   }
   ```

3. Import and instantiate in `app.py`:
   ```python
   from stacks.my_new_stack import MyNewStack

   my_new_stack = MyNewStack(
       app,
       app_context.get_stack_name("MyNew"),
       app_context=app_context,
       env=env,
   )
   ```

## Troubleshooting

### Module Not Found Errors

Ensure the virtual environment is activated:
```bash
source .venv/bin/activate
```

Or use the Makefile commands which handle this automatically.

### AWS Credentials Issues

Verify your AWS profile is configured:
```bash
aws sts get-caller-identity --profile sflt
```

### Config File Not Found

The system looks for `config/app-config-{branch}.json` based on your current git branch.

Create the config file for your branch or set `APP_CONFIG` environment variable:
```bash
export APP_CONFIG=config/app-config-main.json
make synth
```

## Best Practices

1. **Never commit AWS account numbers** - Leave the `Account` field empty in committed configs
2. **Branch-based deployments** - Each branch gets its own isolated environment
3. **Configuration separation** - Keep configs separate from code
4. **Stack independence** - Stacks communicate via SSM Parameter Store (future)
5. **Destructible by default** - Easy cleanup for development environments

## References

- [AWS CDK Python Documentation](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [AWS CDK DevOps Template](https://github.com/aws-samples/aws-cdk-project-template-for-devops)
- [CDK Best Practices](https://docs.aws.amazon.com/cdk/latest/guide/best-practices.html)
