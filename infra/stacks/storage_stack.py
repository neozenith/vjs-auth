"""Storage stack with S3 bucket."""

from aws_cdk import Stack, RemovalPolicy
from aws_cdk import aws_s3 as s3
from constructs import Construct


class StorageStack(Stack):
    """Creates S3 bucket for static website hosting."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_context,
        **kwargs,
    ) -> None:
        """Initialize storage stack.

        Args:
            scope: CDK app or stage
            construct_id: Stack identifier
            app_context: Application context with config
            **kwargs: Additional stack arguments
        """
        super().__init__(scope, construct_id, **kwargs)

        # Get stack configuration
        config = app_context.get_stack_config("Storage")
        bucket_base_name = config.get("BucketName", "storage")

        # Create S3 bucket with branch-based naming
        # Format: {bucket-name}-{stage}
        bucket_name = f"{bucket_base_name}-{app_context.stage}"

        self.bucket = s3.Bucket(
            self,
            "Bucket",
            bucket_name=bucket_name,
            # Enable versioning for better data protection
            versioned=True,
            # Enable encryption at rest
            encryption=s3.BucketEncryption.S3_MANAGED,
            # Block public access by default (modify for static hosting if needed)
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            # For development: allow easy teardown
            # For production: change to RETAIN
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
