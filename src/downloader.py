"""Climate data downloader module for NOAA climate data ingestion.

This module handles downloading, validating, and processing climate data from
NOAA sources (e.g., GHCN-Daily, NCEI Monthly Summaries).
"""

import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ClimateDownloader:
    """Download and validate climate data from NOAA sources."""

    # Valid climate element types from GHCN-Daily
    VALID_ELEMENTS = {
        "PRCP",  # Precipitation
        "TMAX",  # Temperature maximum
        "TMIN",  # Temperature minimum
        "TOBS",  # Temperature at time of observation
        "SNOW",  # Snowfall
        "SNWD",  # Snow depth
        "EVAP",  # Evaporation
        "MXPN",  # Maximum pressure
        "MNPN",  # Minimum pressure
        "PGTM",  # Peak gust time
        "WDMV",  # Wind movement
    }

    def __init__(self, config: dict):
        """Initialize the climate downloader with configuration.

        Args:
            config: Configuration dictionary with required sections:
                - climate: Contains download_dir, source_url, api_key
                - filtering (optional): Station IDs and data types to filter
                - logging: Logging configuration

        Raises:
            KeyError: If required configuration is missing
        """
        self.config = config
        climate_config = config["climate"]

        self.download_dir = Path(climate_config["download_dir"])
        self.source_url = climate_config["source_url"]
        self.api_key = climate_config.get("api_key")

        # Create download directory if it doesn't exist
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Get filtering configuration if present
        filtering_config = config.get("filtering", {})
        self.filter_station_ids = filtering_config.get("station_ids")
        self.filter_data_types = filtering_config.get("data_types")

        logger.info(f"ClimateDownloader initialized with download_dir: {self.download_dir}")

    def load_csv(self, file_path: Path) -> pd.DataFrame:
        """Load climate data from CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            DataFrame containing climate data

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        logger.info(f"Loading CSV file: {file_path}")
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} records from {file_path}")

        return df

    def validate_columns(self, df: pd.DataFrame) -> bool:
        """Validate that required columns exist in dataframe.

        Args:
            df: DataFrame to validate

        Returns:
            True if validation passes

        Raises:
            ValueError: If required columns are missing
        """
        required_columns = {"station_id", "date", "element", "value"}
        missing = required_columns - set(df.columns)

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        logger.debug("Column validation passed")
        return True

    def validate_dates(self, df: pd.DataFrame) -> bool:
        """Validate that dates are in YYYY-MM-DD format.

        Args:
            df: DataFrame with date column

        Returns:
            True if validation passes

        Raises:
            ValueError: If dates are invalid
        """
        try:
            pd.to_datetime(df["date"], format="%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD: {e}")

        logger.debug("Date validation passed")
        return True

    def validate_elements(self, df: pd.DataFrame) -> bool:
        """Validate that element types are valid climate elements.

        Args:
            df: DataFrame with element column

        Returns:
            True if validation passes

        Raises:
            ValueError: If invalid elements are found
        """
        invalid_elements = set(df["element"].unique()) - self.VALID_ELEMENTS
        if invalid_elements:
            raise ValueError(f"Invalid element types: {invalid_elements}")

        logger.debug("Element validation passed")
        return True

    def validate_numeric_values(self, df: pd.DataFrame) -> bool:
        """Validate that value column contains numeric data.

        Args:
            df: DataFrame with value column

        Returns:
            True if validation passes

        Raises:
            ValueError: If non-numeric values found (excluding NaN)
        """
        # Try to convert to numeric, handling NaN
        try:
            pd.to_numeric(df["value"], errors="coerce")
            # Check if any non-NaN values couldn't be converted
            if (df["value"].notna() & pd.to_numeric(df["value"], errors="coerce").isna()).any():
                raise ValueError("Non-numeric values in value column")
        except Exception as e:
            raise ValueError(f"Value column validation failed: {e}")

        logger.debug("Numeric value validation passed")
        return True

    def validate_station_ids(self, df: pd.DataFrame) -> bool:
        """Validate that station IDs are present and non-empty.

        Args:
            df: DataFrame with station_id column

        Returns:
            True if validation passes

        Raises:
            ValueError: If station IDs are missing or empty
        """
        if df["station_id"].isna().any() or (df["station_id"] == "").any():
            raise ValueError("Missing or empty station IDs")

        logger.debug("Station ID validation passed")
        return True

    def validate_data(self, df: pd.DataFrame) -> bool:
        """Run all validation checks on the dataframe.

        Args:
            df: DataFrame to validate

        Returns:
            True if all validations pass

        Raises:
            ValueError: If any validation fails
        """
        self.validate_columns(df)
        self.validate_dates(df)
        self.validate_elements(df)
        self.validate_numeric_values(df)
        self.validate_station_ids(df)

        logger.info(f"All validations passed for {len(df)} records")
        return True

    def filter_by_station_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter dataframe by specific station IDs.

        Args:
            df: DataFrame to filter

        Returns:
            Filtered DataFrame

        Raises:
            ValueError: If configured station IDs not found
        """
        if not self.filter_station_ids:
            return df

        filtered = df[df["station_id"].isin(self.filter_station_ids)].copy()

        logger.info(
            f"Filtered to {len(filtered)} records from "
            f"{len(self.filter_station_ids)} stations"
        )
        return filtered

    def filter_by_element_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter dataframe by specific element types.

        Args:
            df: DataFrame to filter

        Returns:
            Filtered DataFrame
        """
        if not self.filter_data_types:
            return df

        filtered = df[df["element"].isin(self.filter_data_types)].copy()

        logger.info(f"Filtered to {len(filtered)} records from {len(self.filter_data_types)} element types")
        return filtered

    def filter_by_date_range(
        self, df: pd.DataFrame, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Filter dataframe by date range.

        Args:
            df: DataFrame to filter
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)

        Returns:
            Filtered DataFrame
        """
        df_filtered = df.copy()
        df_filtered["date"] = pd.to_datetime(df_filtered["date"])

        mask = (df_filtered["date"] >= start_date) & (df_filtered["date"] <= end_date)
        filtered = df_filtered[mask].copy()

        logger.info(f"Filtered to {len(filtered)} records between {start_date} and {end_date}")
        return filtered

    def save_csv(self, df: pd.DataFrame, output_path: Path) -> None:
        """Save dataframe to CSV file.

        Args:
            df: DataFrame to save
            output_path: Path where CSV will be saved

        Raises:
            IOError: If file write fails
        """
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} records to {output_path}")

    def download_and_validate(self, output_file: Optional[Path] = None) -> pd.DataFrame:
        """Execute complete download and validation workflow.

        This is the main entry point that coordinates:
        1. Load CSV from source
        2. Validate data integrity
        3. Apply filters if configured
        4. Save to output file if specified

        Args:
            output_file: Optional path to save validated data

        Returns:
            Validated and filtered DataFrame

        Raises:
            Various exceptions if any step fails
        """
        logger.info("Starting climate data download and validation workflow")

        # Load CSV
        if self.source_url.startswith("file://"):
            file_path = Path(self.source_url.replace("file://", ""))
        else:
            file_path = Path(self.source_url)

        df = self.load_csv(file_path)

        # Validate
        self.validate_data(df)

        # Apply filters
        df = self.filter_by_station_ids(df)
        df = self.filter_by_element_types(df)

        # Save if output specified
        if output_file:
            self.save_csv(df, output_file)

        logger.info("Download and validation workflow completed successfully")
        return df
