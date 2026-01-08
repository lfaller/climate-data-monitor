"""Pipeline orchestrator for end-to-end climate data quality monitoring.

This module coordinates the complete workflow:
1. Download and validate climate data
2. Assess quality metrics
3. Package and version with Quilt
4. Push to S3 registry
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .downloader import ClimateDownloader
from .quality_checker import QualityChecker
from .quilt_packager import QuiltPackager

logger = logging.getLogger(__name__)

# AWS utilities (optional)
try:
    from ..config.aws_setup import AWSCredentialValidator, S3RegistryConfig
    HAS_AWS = True
except ImportError:
    HAS_AWS = False
    logger.debug("AWS utilities not available - S3 validation will be limited")


class PipelineOrchestrator:
    """Orchestrate the complete climate data monitoring pipeline."""

    def __init__(self, config: Dict, validate_aws: bool = True):
        """Initialize the orchestrator with configuration.

        Args:
            config: Configuration dictionary with sections for climate, quality, and quilt
            validate_aws: Whether to validate AWS credentials if pushing to S3
        """
        self.config = config
        self.timestamp = datetime.utcnow()

        # Initialize pipeline components
        self.downloader = ClimateDownloader(config)
        self.quality_checker = QualityChecker(config)
        self.packager = QuiltPackager(config)

        # Validate AWS credentials if needed
        self.aws_validated = False
        if validate_aws and self.packager.push_enabled:
            self._validate_aws_credentials()

        logger.info(f"PipelineOrchestrator initialized at {self.timestamp.isoformat()}")

    def run(self, data_file: Optional[Path] = None) -> Dict:
        """Execute the complete pipeline.

        This method coordinates all pipeline steps and returns comprehensive results.

        Args:
            data_file: Path to input data file. If None, uses source_url from config

        Returns:
            Dictionary with pipeline results including:
            - success: Whether pipeline completed successfully
            - data_file: Path to processed data
            - quality_report: Quality metrics report
            - package_name: Quilt package name
            - timestamp: Pipeline execution timestamp
            - errors: Any errors encountered (empty if successful)

        Raises:
            Various exceptions from component steps if critical failures occur
        """
        results = {
            "success": False,
            "data_file": None,
            "quality_report": None,
            "package_name": self.packager.package_name,
            "timestamp": self.timestamp.isoformat(),
            "errors": [],
        }

        try:
            logger.info("Starting climate data pipeline")

            # Step 1: Download and validate data
            logger.info("Step 1/4: Downloading and validating climate data")
            processed_data = self._download_and_validate(data_file)
            results["data_file"] = str(processed_data)
            logger.info(f"Downloaded data: {processed_data}")

            # Step 2: Assess quality
            logger.info("Step 2/4: Assessing data quality")
            quality_report = self._assess_quality(processed_data)
            results["quality_report"] = quality_report
            logger.info(
                f"Quality assessment complete. Score: {quality_report['quality_score']:.1f}/100"
            )

            # Step 3: Package data
            logger.info("Step 3/4: Creating Quilt package")
            self._package_data(processed_data, quality_report)
            logger.info(f"Package created: {self.packager.package_name}")

            # Step 4: Push to registry
            logger.info("Step 4/4: Pushing to registry")
            self._push_to_registry()
            logger.info("Package pushed to registry")

            results["success"] = True
            logger.info("Pipeline completed successfully")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            results["errors"].append(str(e))

        return results

    def _download_and_validate(self, data_file: Optional[Path] = None) -> Path:
        """Download and validate climate data.

        Args:
            data_file: Optional explicit data file path

        Returns:
            Path to validated data file

        Raises:
            FileNotFoundError: If data file doesn't exist
            ValueError: If validation fails
        """
        # Use provided file or load from source_url in config
        if data_file is None:
            source_url = self.config["climate"]["source_url"]
            # Handle file:// URLs
            if source_url.startswith("file://"):
                data_file = Path(source_url.replace("file://", ""))
            else:
                raise ValueError(f"Unsupported source URL: {source_url}")

        logger.info(f"Loading data from {data_file}")
        df = self.downloader.load_csv(data_file)

        # Validate data
        self.downloader.validate_columns(df)
        self.downloader.validate_dates(df)
        self.downloader.validate_elements(df)
        self.downloader.validate_numeric_values(df)
        self.downloader.validate_station_ids(df)

        # Apply filtering if configured
        filtering_config = self.config.get("filtering", {})
        if filtering_config.get("enabled", False):
            if filtering_config.get("station_ids"):
                df = self.downloader.filter_by_station_ids(df, filtering_config["station_ids"])
            if filtering_config.get("data_types"):
                df = self.downloader.filter_by_element_types(df, filtering_config["data_types"])

        # Save processed data
        output_file = self._get_output_filename()
        df.to_csv(output_file, index=False)
        logger.info(f"Processed data saved to {output_file}")

        return output_file

    def _assess_quality(self, data_file: Path) -> Dict:
        """Assess quality of climate data.

        Args:
            data_file: Path to validated data file

        Returns:
            Quality metrics report dictionary
        """
        df = self.downloader.load_csv(data_file)
        report = self.quality_checker.generate_quality_report(df)

        # Save report to JSON
        report_file = self.quality_checker.output_dir / f"quality_report_{self.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Quality report saved to {report_file}")
        return report

    def _package_data(self, data_file: Path, quality_report: Dict) -> None:
        """Package data and quality report with Quilt.

        Args:
            data_file: Path to processed data file
            quality_report: Quality metrics report
        """
        # Use the full_package_workflow which handles all steps
        self.packager.full_package_workflow(data_file, quality_report)

    def _push_to_registry(self) -> None:
        """Push package to registry (S3 or local).

        This is handled within full_package_workflow, but provided as a separate
        method for potential retry logic or additional validation.
        """
        # Package is already pushed as part of full_package_workflow
        logger.info("Registry push completed")

    def _get_output_filename(self) -> Path:
        """Generate output filename with timestamp.

        Returns:
            Path for processed data file
        """
        download_dir = Path(self.config["climate"]["download_dir"])
        timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"climate_data_processed_{timestamp_str}.csv"
        return download_dir / filename

    def _validate_aws_credentials(self) -> None:
        """Validate AWS credentials for S3 registry access.

        Called during initialization if push_to_registry is enabled.

        Raises:
            Exception: If AWS credentials cannot be validated
        """
        if not HAS_AWS:
            logger.warning("AWS utilities not available - skipping credential validation")
            return

        try:
            aws_config = self.config.get("aws", {})
            region = aws_config.get("region", "us-west-2")

            validator = AWSCredentialValidator(region=region)

            # Validate credentials
            validator.validate_credentials()
            logger.info("AWS credentials validated successfully")

            # Test bucket access if configured
            if aws_config.get("test_bucket_access", True):
                bucket_name = self.config["quilt"]["bucket"]
                try:
                    validator.test_bucket_access(bucket_name)
                    logger.info(f"S3 bucket access verified: {bucket_name}")
                except Exception as e:
                    logger.error(f"Could not access S3 bucket {bucket_name}: {e}")
                    raise

            self.aws_validated = True

        except Exception as e:
            logger.error(f"AWS validation failed: {e}")
            raise

    def get_status_report(self, results: Dict) -> str:
        """Generate human-readable status report.

        Args:
            results: Results dictionary from run()

        Returns:
            Formatted status report string
        """
        status = "✓ SUCCESS" if results["success"] else "✗ FAILED"
        report = f"\n{'='*60}\n"
        report += f"Climate Data Monitor - Pipeline Execution Report\n"
        report += f"{'='*60}\n"
        report += f"Status: {status}\n"
        report += f"Timestamp: {results['timestamp']}\n"
        report += f"Package: {results['package_name']}\n"

        if results["data_file"]:
            report += f"Data File: {results['data_file']}\n"

        if results["quality_report"]:
            quality = results["quality_report"]
            report += f"\nQuality Metrics:\n"
            report += f"  Quality Score: {quality.get('quality_score', 'N/A')}/100\n"
            report += f"  Rows: {quality.get('row_count', 'N/A')}\n"
            report += f"  Null %: {quality.get('null_percentage_avg', 'N/A'):.2f}%\n"
            report += f"  Stations: {quality.get('station_count', 'N/A')}\n"

        if results["errors"]:
            report += f"\nErrors:\n"
            for error in results["errors"]:
                report += f"  - {error}\n"

        report += f"{'='*60}\n"
        return report
