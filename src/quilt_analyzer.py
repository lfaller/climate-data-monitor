"""Utility for analyzing Quilt packages from the climate data monitor.

This module provides tools to inspect, analyze, and export data from
locally stored Quilt packages created by the pipeline.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import quilt3

logger = logging.getLogger(__name__)


class QuiltPackageAnalyzer:
    """Analyze and inspect Quilt climate data packages."""

    def __init__(self, package_name: str, registry: Optional[str] = None):
        """Initialize the analyzer with a package name.

        Args:
            package_name: Full package name (e.g., "climate/demo-sample")
            registry: Optional registry URL (e.g., "s3://my-bucket")
                     If not provided, uses default local Quilt registry
        """
        self.package_name = package_name
        self.registry = registry
        self.package = None
        self.data = None
        self._load_package()

    def _load_package(self) -> None:
        """Load the package from Quilt storage (local or S3)."""
        try:
            if self.registry:
                logger.info(f"Loading from registry: {self.registry}")
                self.package = quilt3.Package.browse(
                    self.package_name, registry=self.registry
                )
            else:
                self.package = quilt3.Package.browse(self.package_name)
            logger.info(f"Loaded package: {self.package_name}")
        except Exception as e:
            logger.error(f"Failed to load package {self.package_name}: {e}")
            raise

    def get_metadata(self) -> Dict:
        """Get package metadata.

        Returns:
            Dictionary of metadata from the package
        """
        if not self.package:
            raise RuntimeError("Package not loaded")
        return dict(self.package.meta)

    def get_data_files(self) -> List[str]:
        """Get list of data files in the package.

        Returns:
            List of file names in the package
        """
        if not self.package:
            raise RuntimeError("Package not loaded")
        return list(self.package.keys())

    def load_data(self, file_key: Optional[str] = None) -> pd.DataFrame:
        """Load data from the package.

        Args:
            file_key: Specific file to load. If None, loads first CSV file.

        Returns:
            DataFrame with the package data
        """
        if not self.package:
            raise RuntimeError("Package not loaded")

        if file_key is None:
            # Get first CSV file
            csv_files = [k for k in self.package.keys() if k.endswith('.csv')]
            if not csv_files:
                raise ValueError("No CSV files found in package")
            file_key = csv_files[0]

        logger.info(f"Loading data from {file_key}")
        self.data = self.package[file_key]()
        return self.data

    def get_quality_metrics(self) -> Dict:
        """Extract quality metrics from package metadata.

        Returns:
            Dictionary of quality metrics
        """
        metadata = self.get_metadata()
        return {
            "quality_score": metadata.get("quality_score"),
            "row_count": metadata.get("row_count"),
            "null_percentage_avg": metadata.get("null_percentage_avg"),
            "duplicate_count": metadata.get("duplicate_count"),
            "station_count": metadata.get("station_count"),
            "timestamp": metadata.get("timestamp"),
        }

    def get_temperature_stats(self) -> Dict:
        """Extract temperature statistics from metadata.

        Returns:
            Dictionary of temperature statistics
        """
        metadata = self.get_metadata()
        return metadata.get("temperature_range", {})

    def get_precipitation_stats(self) -> Dict:
        """Extract precipitation statistics from metadata.

        Returns:
            Dictionary of precipitation statistics
        """
        metadata = self.get_metadata()
        return metadata.get("precipitation_stats", {})

    def print_summary(self) -> None:
        """Print a formatted summary of the package."""
        print("\n" + "=" * 70)
        print(f"Quilt Package Analysis: {self.package_name}")
        print("=" * 70)

        # Quality metrics
        print("\nQuality Metrics:")
        metrics = self.get_quality_metrics()
        for key, value in metrics.items():
            if value is not None:
                print(f"  {key}: {value}")

        # Temperature stats
        print("\nTemperature Statistics:")
        temp_stats = self.get_temperature_stats()
        for key, value in temp_stats.items():
            print(f"  {key}: {value}")

        # Precipitation stats
        print("\nPrecipitation Statistics:")
        prcp_stats = self.get_precipitation_stats()
        for key, value in prcp_stats.items():
            print(f"  {key}: {value}")

        # Data files
        print("\nData Files:")
        for file_name in self.get_data_files():
            print(f"  - {file_name}")

        print("\n" + "=" * 70 + "\n")

    def export_metadata_to_json(self, output_file: Path) -> None:
        """Export package metadata to JSON file.

        Args:
            output_file: Path to output JSON file
        """
        metadata = self.get_metadata()
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Exported metadata to {output_file}")

    def export_data_to_csv(
        self, output_file: Path, file_key: Optional[str] = None
    ) -> None:
        """Export package data to CSV file.

        Args:
            output_file: Path to output CSV file
            file_key: Specific file to export. If None, exports first CSV.
        """
        data = self.load_data(file_key)
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data.to_csv(output_file, index=False)
        logger.info(f"Exported data to {output_file}")

    def get_data_summary(self) -> Dict:
        """Get statistical summary of the data.

        Returns:
            Dictionary with data summary statistics
        """
        if self.data is None:
            self.load_data()

        return {
            "shape": self.data.shape,
            "columns": list(self.data.columns),
            "dtypes": self.data.dtypes.to_dict(),
            "missing_values": self.data.isnull().sum().to_dict(),
            "unique_elements": self.data.get("element", pd.Series()).unique().tolist()
            if "element" in self.data.columns
            else [],
            "unique_stations": self.data.get("station_id", pd.Series()).nunique()
            if "station_id" in self.data.columns
            else 0,
        }
