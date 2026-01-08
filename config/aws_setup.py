"""AWS S3 configuration and credential validation utilities.

This module helps set up and validate AWS credentials for pushing to S3 registries.
"""

import logging
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class AWSCredentialValidator:
    """Validate and manage AWS credentials for S3 registry access."""

    def __init__(self, region: str = "us-west-2"):
        """Initialize the validator.

        Args:
            region: AWS region for S3 bucket
        """
        self.region = region
        self.s3_client = None
        self.credentials_valid = False

    def validate_credentials(self) -> bool:
        """Validate AWS credentials are available and functional.

        Attempts to list S3 buckets to verify credentials work.

        Returns:
            True if credentials are valid and working

        Raises:
            NoCredentialsError: If no AWS credentials found
            BotoCoreError: If credential validation fails
        """
        try:
            self.s3_client = boto3.client("s3", region_name=self.region)

            # Try to list buckets to validate credentials
            response = self.s3_client.list_buckets()
            bucket_count = len(response.get("Buckets", []))

            logger.info(f"AWS credentials validated. Found {bucket_count} accessible buckets.")
            self.credentials_valid = True
            return True

        except NoCredentialsError:
            logger.error(
                "No AWS credentials found. Please configure AWS credentials using:\n"
                "  - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables\n"
                "  - ~/.aws/credentials file\n"
                "  - AWS IAM role (if running on EC2/ECS)"
            )
            raise

        except BotoCoreError as e:
            logger.error(f"AWS credential validation failed: {e}")
            raise

        except ClientError as e:
            logger.error(f"S3 access error: {e}")
            raise

    def test_bucket_access(self, bucket_name: str) -> bool:
        """Test if we have access to a specific S3 bucket.

        Args:
            bucket_name: Name of the S3 bucket to test

        Returns:
            True if bucket is accessible

        Raises:
            ClientError: If bucket doesn't exist or access is denied
        """
        if not self.s3_client:
            self.validate_credentials()

        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"S3 bucket access verified: {bucket_name}")
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")

            if error_code == "404":
                logger.error(f"S3 bucket not found: {bucket_name}")
            elif error_code == "403":
                logger.error(f"Access denied to S3 bucket: {bucket_name}")
            else:
                logger.error(f"Error accessing bucket {bucket_name}: {e}")

            raise

    def get_session(self) -> Optional[boto3.Session]:
        """Get a boto3 session with validated credentials.

        Returns:
            Configured boto3 Session object

        Raises:
            NoCredentialsError: If credentials cannot be validated
        """
        if not self.credentials_valid:
            self.validate_credentials()

        return boto3.Session(region_name=self.region)


class S3RegistryConfig:
    """Configuration helper for S3-based Quilt registries."""

    @staticmethod
    def format_registry_url(bucket_name: str, region: str = "us-west-2") -> str:
        """Format a standard S3 registry URL.

        Args:
            bucket_name: Name of the S3 bucket
            region: AWS region (default: us-west-2)

        Returns:
            Formatted S3 registry URL

        Example:
            >>> S3RegistryConfig.format_registry_url("my-climate-bucket")
            's3://my-climate-bucket'
        """
        return f"s3://{bucket_name}"

    @staticmethod
    def validate_bucket_name(bucket_name: str) -> bool:
        """Validate S3 bucket naming conventions.

        Args:
            bucket_name: Bucket name to validate

        Returns:
            True if bucket name is valid

        Raises:
            ValueError: If bucket name doesn't meet S3 requirements
        """
        if not bucket_name or len(bucket_name) < 3 or len(bucket_name) > 63:
            raise ValueError("Bucket name must be 3-63 characters long")

        if not all(c.isalnum() or c in "-." for c in bucket_name):
            raise ValueError("Bucket name can only contain alphanumeric characters, hyphens, and dots")

        if bucket_name.startswith("-") or bucket_name.endswith("-"):
            raise ValueError("Bucket name cannot start or end with a hyphen")

        if ".." in bucket_name or "-." in bucket_name or ".-" in bucket_name:
            raise ValueError("Bucket name cannot have consecutive dots or hyphens adjacent to dots")

        return True


def create_s3_config_template() -> dict:
    """Create a template for S3-based Quilt configuration.

    Returns:
        Configuration dictionary template for S3 registry
    """
    return {
        "quilt": {
            "bucket": "your-climate-data-bucket",
            "package_name": "climate/data",
            "registry": "s3://your-climate-data-bucket",
            "push_to_registry": True,
            "region": "us-west-2",
        },
        "aws": {
            "region": "us-west-2",
            "validate_credentials": True,
            "test_bucket_access": True,
        },
    }
