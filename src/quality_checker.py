"""Quality checking module for climate data quality assessment.

This module calculates climate-specific quality metrics including:
- Data completeness (null percentages)
- Temperature statistics and outlier detection
- Precipitation statistics and extreme value detection
- Geographic coverage (station counts, new/inactive stations)
- Overall quality scoring
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class QualityChecker:
    """Calculate quality metrics for climate data."""

    def __init__(self, config: dict):
        """Initialize the quality checker with configuration.

        Args:
            config: Configuration dictionary with required sections:
                - quality: Contains thresholds and output_dir
                - logging: Logging configuration

        Raises:
            KeyError: If required configuration is missing
        """
        self.config = config
        quality_config = config["quality"]
        thresholds = quality_config["thresholds"]

        # Store thresholds
        self.min_quality_score = thresholds.get("min_quality_score", 75)
        self.max_null_percentage = thresholds.get("max_null_percentage", 15)
        self.max_outlier_percentage = thresholds.get("max_outlier_percentage", 5)
        self.temp_outlier_std_dev = thresholds.get("temp_outlier_std_dev", 3)
        self.temp_min_valid = thresholds.get("temp_min_valid", -60)
        self.temp_max_valid = thresholds.get("temp_max_valid", 60)
        self.precip_max_daily = thresholds.get("precip_max_daily", 500)

        # Create output directory
        self.output_dir = Path(quality_config["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"QualityChecker initialized with output_dir: {self.output_dir}")

    def calculate_null_percentage(self, df: pd.DataFrame) -> float:
        """Calculate percentage of null values in value column.

        Args:
            df: DataFrame to analyze

        Returns:
            Percentage of null values (0-100)
        """
        if len(df) == 0:
            return 0.0

        null_count = df["value"].isna().sum()
        null_pct = (null_count / len(df)) * 100

        logger.debug(f"Null percentage: {null_pct:.2f}%")
        return null_pct

    def count_duplicates(self, df: pd.DataFrame) -> int:
        """Count duplicate records.

        Args:
            df: DataFrame to analyze

        Returns:
            Number of duplicate rows
        """
        dup_mask = df.duplicated(subset=["station_id", "date", "element"], keep=False)
        dup_count = dup_mask.sum() - df.duplicated(subset=["station_id", "date", "element"]).sum()

        logger.debug(f"Found {dup_count} duplicate records")
        return int(dup_count)

    def calculate_temperature_statistics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate temperature statistics (min, max, mean).

        Args:
            df: DataFrame with temperature data

        Returns:
            Dictionary with temperature statistics
        """
        # Filter to temperature elements only
        temp_df = df[df["element"].isin(["TMAX", "TMIN", "TOBS"])].copy()

        if len(temp_df) == 0:
            return {
                "tmax_min": None,
                "tmax_max": None,
                "tmax_mean": None,
                "tmin_min": None,
                "tmin_max": None,
                "tmin_mean": None,
            }

        stats = {}

        for element in ["TMAX", "TMIN"]:
            element_data = temp_df[temp_df["element"] == element]["value"].dropna()
            if len(element_data) > 0:
                key = element.lower()
                stats[f"{key}_min"] = float(element_data.min())
                stats[f"{key}_max"] = float(element_data.max())
                stats[f"{key}_mean"] = float(element_data.mean())
            else:
                key = element.lower()
                stats[f"{key}_min"] = None
                stats[f"{key}_max"] = None
                stats[f"{key}_mean"] = None

        logger.debug(f"Temperature statistics: {stats}")
        return stats

    def detect_temperature_outliers(self, df: pd.DataFrame) -> int:
        """Detect temperature values that are outliers (>3 std dev from mean).

        Args:
            df: DataFrame with temperature data

        Returns:
            Number of outlier records
        """
        temp_df = df[df["element"].isin(["TMAX", "TMIN", "TOBS"])].copy()
        temp_df["value"] = pd.to_numeric(temp_df["value"], errors="coerce")

        outlier_count = 0

        for element in ["TMAX", "TMIN"]:
            element_data = temp_df[temp_df["element"] == element]["value"].dropna()
            if len(element_data) > 1:
                mean = element_data.mean()
                std = element_data.std()
                outliers = ((element_data - mean).abs() > self.temp_outlier_std_dev * std).sum()
                outlier_count += int(outliers)

        logger.debug(f"Found {outlier_count} temperature outliers")
        return int(outlier_count)

    def validate_temperature_range(self, df: pd.DataFrame) -> bool:
        """Validate that temperatures are within valid range.

        Args:
            df: DataFrame with temperature data

        Returns:
            True if all temperatures are valid

        Raises:
            ValueError: If invalid temperatures found
        """
        temp_df = df[df["element"].isin(["TMAX", "TMIN", "TOBS"])].copy()
        temp_df["value"] = pd.to_numeric(temp_df["value"], errors="coerce")

        invalid = temp_df[
            (temp_df["value"] < self.temp_min_valid) | (temp_df["value"] > self.temp_max_valid)
        ]

        if len(invalid) > 0:
            raise ValueError(
                f"Invalid temperature values found: {len(invalid)} records "
                f"outside range [{self.temp_min_valid}, {self.temp_max_valid}]"
            )

        logger.debug("Temperature range validation passed")
        return True

    def detect_missing_days(
        self, df: pd.DataFrame, start_date: str, end_date: str
    ) -> int:
        """Detect missing days in the data range for each station.

        Args:
            df: DataFrame with date column
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Total number of missing days across all stations
        """
        df["date"] = pd.to_datetime(df["date"])
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        total_days = (end - start).days + 1
        unique_dates = df["date"].unique()
        days_in_data = len(unique_dates)
        missing_days = total_days - days_in_data

        logger.debug(f"Missing days: {missing_days} out of {total_days}")
        return max(0, int(missing_days))

    def calculate_precipitation_statistics(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate precipitation statistics (min, max, mean).

        Args:
            df: DataFrame with precipitation data

        Returns:
            Dictionary with precipitation statistics
        """
        prcp_df = df[df["element"] == "PRCP"].copy()
        prcp_df["value"] = pd.to_numeric(prcp_df["value"], errors="coerce")
        prcp_data = prcp_df["value"].dropna()

        if len(prcp_data) == 0:
            return {"prcp_min": None, "prcp_max": None, "prcp_mean": None}

        stats = {
            "prcp_min": float(prcp_data.min()),
            "prcp_max": float(prcp_data.max()),
            "prcp_mean": float(prcp_data.mean()),
        }

        logger.debug(f"Precipitation statistics: {stats}")
        return stats

    def calculate_zero_precipitation_percentage(self, df: pd.DataFrame) -> float:
        """Calculate percentage of days with zero precipitation (normal).

        Args:
            df: DataFrame with precipitation data

        Returns:
            Percentage of zero precipitation days (0-100)
        """
        prcp_df = df[df["element"] == "PRCP"].copy()
        prcp_df["value"] = pd.to_numeric(prcp_df["value"], errors="coerce")

        if len(prcp_df) == 0:
            return 0.0

        zero_count = (prcp_df["value"] == 0.0).sum()
        zero_pct = (zero_count / len(prcp_df)) * 100

        logger.debug(f"Zero precipitation percentage: {zero_pct:.2f}%")
        return float(zero_pct)

    def detect_precipitation_extremes(self, df: pd.DataFrame) -> int:
        """Detect extreme precipitation values (> threshold).

        Args:
            df: DataFrame with precipitation data

        Returns:
            Number of extreme precipitation records
        """
        prcp_df = df[df["element"] == "PRCP"].copy()
        prcp_df["value"] = pd.to_numeric(prcp_df["value"], errors="coerce")

        extremes = (prcp_df["value"] > self.precip_max_daily).sum()

        logger.debug(f"Found {extremes} extreme precipitation values")
        return int(extremes)

    def count_active_stations(self, df: pd.DataFrame) -> int:
        """Count number of active (reporting) stations.

        Args:
            df: DataFrame with station_id column

        Returns:
            Number of unique stations
        """
        active_count = df["station_id"].nunique()
        logger.debug(f"Active stations: {active_count}")
        return int(active_count)

    def detect_new_stations(
        self, df_current: pd.DataFrame, df_previous: pd.DataFrame
    ) -> List[str]:
        """Detect stations that are new in current data.

        Args:
            df_current: Current period dataframe
            df_previous: Previous period dataframe

        Returns:
            List of new station IDs
        """
        current_stations = set(df_current["station_id"].unique())
        previous_stations = set(df_previous["station_id"].unique())

        new_stations = list(current_stations - previous_stations)
        logger.debug(f"Found {len(new_stations)} new stations")
        return new_stations

    def detect_inactive_stations(
        self, df_current: pd.DataFrame, df_previous: pd.DataFrame
    ) -> List[str]:
        """Detect stations that were active but are now inactive.

        Args:
            df_current: Current period dataframe
            df_previous: Previous period dataframe

        Returns:
            List of inactive station IDs
        """
        current_stations = set(df_current["station_id"].unique())
        previous_stations = set(df_previous["station_id"].unique())

        inactive_stations = list(previous_stations - current_stations)
        logger.debug(f"Found {len(inactive_stations)} inactive stations")
        return inactive_stations

    def calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate overall quality score (0-100).

        Scoring breakdown (from PROJECT_PLAN.md):
        - Completeness: 30 points (max 15% null)
        - Outlier rate: 25 points (max 5% outliers)
        - Temperature range validity: 10 points
        - Geographic coverage: 25 points (station reporting)
        - Schema stability: 10 points

        Args:
            df: DataFrame to score

        Returns:
            Quality score (0-100)
        """
        if len(df) == 0:
            return 0.0

        score = 0.0

        # Completeness (30 points)
        null_pct = self.calculate_null_percentage(df)
        completeness_score = max(0, 30 * (1 - (null_pct / self.max_null_percentage)))
        score += completeness_score

        # Outlier detection (25 points)
        temp_outliers = self.detect_temperature_outliers(df)
        total_temps = len(df[df["element"].isin(["TMAX", "TMIN"])])
        outlier_pct = (temp_outliers / total_temps * 100) if total_temps > 0 else 0
        outlier_score = max(0, 25 * (1 - (outlier_pct / self.max_outlier_percentage)))
        score += outlier_score

        # Temperature range validity (10 points)
        try:
            self.validate_temperature_range(df)
            score += 10
        except ValueError:
            score += 0

        # Geographic coverage (25 points)
        # More stations = better coverage
        station_count = self.count_active_stations(df)
        coverage_score = min(25, station_count * 2)
        score += coverage_score

        # Schema stability (10 points)
        # Check if all required columns present
        required_cols = {"station_id", "date", "element", "value"}
        if required_cols.issubset(set(df.columns)):
            score += 10

        final_score = min(100, score)
        logger.info(f"Quality score calculated: {final_score:.2f}")
        return float(final_score)

    def generate_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive quality report for dataset.

        Args:
            df: DataFrame to assess

        Returns:
            Dictionary with quality metrics and assessment
        """
        logger.info("Generating quality report")

        report = {
            "timestamp": datetime.now().isoformat(),
            "row_count": len(df),
            "column_count": len(df.columns),
            "quality_score": self.calculate_quality_score(df),
            "null_percentage_avg": self.calculate_null_percentage(df),
            "duplicate_count": self.count_duplicates(df),
            "station_count": self.count_active_stations(df),
            "temperature_range": self.calculate_temperature_statistics(df),
            "temperature_outliers": self.detect_temperature_outliers(df),
            "precipitation_stats": self.calculate_precipitation_statistics(df),
            "precipitation_zero_pct": self.calculate_zero_precipitation_percentage(df),
            "precipitation_extremes": self.detect_precipitation_extremes(df),
        }

        logger.info(f"Quality report generated with score: {report['quality_score']:.2f}")
        return report

    def save_quality_report(self, report: Dict[str, Any]) -> Path:
        """Save quality report to JSON file.

        Args:
            report: Quality report dictionary

        Returns:
            Path to saved report file
        """
        timestamp = report["timestamp"].replace(":", "-").replace(".", "-")
        report_file = self.output_dir / f"quality_report_{timestamp}.json"

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Quality report saved to {report_file}")
        return report_file

    def assess_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute complete quality assessment workflow.

        Args:
            df: DataFrame to assess

        Returns:
            Quality report dictionary
        """
        logger.info("Starting quality assessment workflow")

        # Generate report
        report = self.generate_quality_report(df)

        # Save report
        self.save_quality_report(report)

        logger.info("Quality assessment workflow completed")
        return report
