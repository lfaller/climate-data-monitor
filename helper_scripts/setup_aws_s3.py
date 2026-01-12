#!/usr/bin/env python
"""AWS S3 setup helper for Climate Data Monitor.

This script helps set up an S3 bucket for use as a Quilt registry and generates
a production configuration file.

Usage:
    poetry run python helper_scripts/setup_aws_s3.py \
        --bucket-name my-climate-data-bucket \
        --region us-west-2

    # Or interactive mode (no args):
    poetry run python helper_scripts/setup_aws_s3.py
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import boto3
import yaml
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError


def validate_aws_credentials() -> bool:
    """Validate that AWS credentials are available.

    Returns:
        True if credentials are valid

    Raises:
        NoCredentialsError: If no AWS credentials found
    """
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        account_id = identity["Account"]
        user_arn = identity["Arn"]

        print(f"✅ AWS credentials validated")
        print(f"   Account ID: {account_id}")
        print(f"   User/Role: {user_arn}")
        return True

    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("\nPlease configure AWS credentials using one of:")
        print("  1. export AWS_ACCESS_KEY_ID=... && export AWS_SECRET_ACCESS_KEY=...")
        print("  2. aws configure (creates ~/.aws/credentials)")
        print("  3. Use an IAM role (if running on EC2/ECS)")
        raise

    except Exception as e:
        print(f"❌ Error validating credentials: {e}")
        raise


def bucket_exists(bucket_name: str, region: str) -> bool:
    """Check if S3 bucket exists.

    Args:
        bucket_name: Name of the bucket
        region: AWS region

    Returns:
        True if bucket exists
    """
    try:
        s3 = boto3.client("s3", region_name=region)
        s3.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def create_bucket(bucket_name: str, region: str) -> bool:
    """Create S3 bucket for Quilt registry.

    Args:
        bucket_name: Name of the bucket to create
        region: AWS region

    Returns:
        True if bucket was created

    Raises:
        ClientError: If bucket creation fails
    """
    try:
        s3 = boto3.client("s3", region_name=region)

        # Create bucket
        if region == "us-east-1":
            # us-east-1 doesn't need LocationConstraint
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region},
            )

        print(f"✅ S3 bucket created: {bucket_name}")

        # Enable versioning (important for Quilt)
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={"Status": "Enabled"},
        )
        print(f"✅ Versioning enabled on bucket")

        # Block public access (security best practice)
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        print(f"✅ Public access blocked")

        return True

    except ClientError as e:
        if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
            print(f"ℹ️  Bucket already exists and is owned by you: {bucket_name}")
            return False
        elif e.response["Error"]["Code"] == "BucketAlreadyExists":
            print(f"❌ Bucket name already taken (globally unique): {bucket_name}")
            print("   Try a different bucket name (must be globally unique)")
            raise
        else:
            print(f"❌ Error creating bucket: {e}")
            raise


def test_bucket_access(bucket_name: str, region: str) -> bool:
    """Test read/write access to bucket.

    Args:
        bucket_name: Name of the bucket
        region: AWS region

    Returns:
        True if access is verified

    Raises:
        ClientError: If access test fails
    """
    try:
        s3 = boto3.client("s3", region_name=region)

        # Test write
        test_key = ".test-access"
        test_data = b"test access verification"

        s3.put_object(Bucket=bucket_name, Key=test_key, Body=test_data)
        print(f"✅ Write access verified")

        # Test read
        response = s3.get_object(Bucket=bucket_name, Key=test_key)
        retrieved_data = response["Body"].read()

        if retrieved_data == test_data:
            print(f"✅ Read access verified")
        else:
            print(f"❌ Read data mismatch")
            return False

        # Clean up
        s3.delete_object(Bucket=bucket_name, Key=test_key)
        print(f"✅ Cleanup completed")

        return True

    except ClientError as e:
        print(f"❌ Access test failed: {e}")
        raise


def generate_production_config(
    bucket_name: str, region: str, output_file: Path
) -> None:
    """Generate production configuration file.

    Args:
        bucket_name: S3 bucket name
        region: AWS region
        output_file: Path to output config file
    """
    config = {
        "climate": {
            "source_url": "file://data/real_nyc_2024.csv",
            "api_key": None,
            "download_dir": "data/downloads",
            "dataset_id": "OPEN_METEO",
            "geographic_scope": "production",
        },
        "filtering": {
            "enabled": False,
            "station_ids": None,
            "data_types": None,
        },
        "quality": {
            "thresholds": {
                "min_quality_score": 75,
                "max_null_percentage": 15,
                "max_outlier_percentage": 5,
                "max_drift_percentage": 20,
                "temp_outlier_std_dev": 3,
                "temp_min_valid": -60,
                "temp_max_valid": 60,
                "precip_max_daily": 500,
                "precip_outlier_std_dev": 4,
            },
            "output_dir": "output/quality_reports",
        },
        "quilt": {
            "bucket": bucket_name,
            "package_name": "climate/data",
            "registry": f"s3://{bucket_name}",
            "push_to_registry": True,
            "region": region,
        },
        "aws": {
            "region": region,
            "validate_credentials": True,
            "test_bucket_access": True,
        },
        "alerts": {
            "enabled": False,
            "email": None,
            "slack_webhook": None,
        },
        "scheduling": {
            "check_interval_days": 30,
            "auto_run": False,
        },
        "logging": {
            "level": "INFO",
            "log_dir": "logs",
            "file_logging": True,
            "console_logging": True,
        },
    }

    # Write config file
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"✅ Configuration saved: {output_file}")
    print(f"\n   Next step: Update 'climate.source_url' in the config to your data file")


def print_summary(bucket_name: str, region: str, config_file: Path) -> None:
    """Print setup summary and next steps.

    Args:
        bucket_name: S3 bucket name
        region: AWS region
        config_file: Path to generated config
    """
    print("\n" + "=" * 70)
    print("AWS S3 SETUP COMPLETE")
    print("=" * 70)

    print(f"\n✅ S3 Registry Ready")
    print(f"   Bucket: {bucket_name}")
    print(f"   Region: {region}")
    print(f"   URL: s3://{bucket_name}")

    print(f"\n✅ Configuration Generated")
    print(f"   File: {config_file}")

    print(f"\n📝 Next Steps:")
    print(f"   1. Review the generated config file:")
    print(f"      cat {config_file}")
    print(f"\n   2. Update data source if needed:")
    print(f"      # Edit 'climate.source_url' in {config_file}")
    print(f"\n   3. Run the pipeline with S3 push enabled:")
    print(f"      poetry run python -m src run --config {config_file}")
    print(f"\n   4. Verify package in S3 registry:")
    print(f"      poetry run python -m src analyze climate/data")

    print(f"\n💡 Testing the Pipeline:")
    print(f"   # Test with demo data (local, no S3):")
    print(f"   poetry run python -m src run --config config/demo_config.yaml")
    print(f"\n   # Push to S3 with production config:")
    print(f"   poetry run python -m src run --config {config_file} --push")

    print(f"\n🔐 Security Notes:")
    print(f"   - Bucket is versioned (for data governance)")
    print(f"   - Public access is blocked")
    print(f"   - Use IAM roles in production (not access keys)")
    print(f"   - Enable CloudTrail for audit logging")

    print(f"\n" + "=" * 70)


def interactive_setup() -> tuple[str, str, Path]:
    """Run interactive setup prompts.

    Returns:
        Tuple of (bucket_name, region, config_file_path)
    """
    print("\n" + "=" * 70)
    print("AWS S3 SETUP FOR CLIMATE DATA MONITOR")
    print("=" * 70)

    # Get bucket name
    print("\n📦 S3 Bucket Setup")
    print("(Bucket name must be globally unique across all AWS accounts)")

    default_bucket = "climate-data-monitor-quilt"
    bucket_name = input(f"Bucket name [{default_bucket}]: ").strip() or default_bucket

    # Get region
    print("\n🌍 AWS Region")
    default_region = "us-west-2"
    region = input(f"Region [{default_region}]: ").strip() or default_region

    # Get config file path
    print("\n📋 Configuration File")
    default_config = Path("config/production_config.yaml")
    config_input = input(f"Config file path [{default_config}]: ").strip()
    config_file = Path(config_input) if config_input else default_config

    return bucket_name, region, config_file


def main() -> int:
    """Main setup flow.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Set up AWS S3 for Climate Data Monitor Quilt registry"
    )
    parser.add_argument(
        "--bucket-name",
        type=str,
        help="S3 bucket name (must be globally unique)",
    )
    parser.add_argument(
        "--region",
        type=str,
        default="us-west-2",
        help="AWS region (default: us-west-2)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/production_config.yaml"),
        help="Output config file path",
    )
    parser.add_argument(
        "--skip-bucket-create",
        action="store_true",
        help="Skip bucket creation (assumes it already exists)",
    )

    args = parser.parse_args()

    # Use interactive mode if bucket name not provided
    if not args.bucket_name:
        bucket_name, region, config_file = interactive_setup()
    else:
        bucket_name = args.bucket_name
        region = args.region
        config_file = args.config

    try:
        print("\n" + "=" * 70)
        print("STEP 1: Validating AWS Credentials")
        print("=" * 70)
        validate_aws_credentials()

        print("\n" + "=" * 70)
        print("STEP 2: Setting Up S3 Bucket")
        print("=" * 70)

        if args.skip_bucket_create:
            print(f"ℹ️  Skipping bucket creation (--skip-bucket-create)")
            if not bucket_exists(bucket_name, region):
                print(f"❌ Bucket does not exist: {bucket_name}")
                return 1
            print(f"✅ Bucket exists: {bucket_name}")
        else:
            if bucket_exists(bucket_name, region):
                print(f"ℹ️  Bucket already exists: {bucket_name}")
            else:
                create_bucket(bucket_name, region)

        print("\n" + "=" * 70)
        print("STEP 3: Testing Bucket Access")
        print("=" * 70)
        test_bucket_access(bucket_name, region)

        print("\n" + "=" * 70)
        print("STEP 4: Generating Configuration")
        print("=" * 70)
        generate_production_config(bucket_name, region, config_file)

        print_summary(bucket_name, region, config_file)

        return 0

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
