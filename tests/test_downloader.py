"""Tests for ClimateDownloader module.

Tests cover:
- CSV parsing and validation
- Data integrity checks
- Error handling
- File operations
- Data transformation
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.downloader import ClimateDownloader


class TestClimateDownloaderInitialization:
    """Test ClimateDownloader initialization and configuration."""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        config = {
            "climate": {
                "download_dir": "data/downloads",
                "source_url": "file://data/sample_climate_data.csv",
                "api_key": "test_key",
            },
            "logging": {"level": "INFO"},
        }
        downloader = ClimateDownloader(config)
        assert downloader.config == config
        assert downloader.download_dir == Path("data/downloads")

    def test_init_creates_download_directory(self):
        """Test that initialization creates download directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir + "/downloads",
                    "source_url": "file://sample.csv",
                    "api_key": "test_key",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)
            assert downloader.download_dir.exists()

    def test_init_with_missing_climate_config(self):
        """Test initialization fails with missing climate config."""
        config = {"logging": {"level": "INFO"}}
        with pytest.raises(KeyError):
            ClimateDownloader(config)

    def test_init_with_missing_download_dir(self):
        """Test initialization fails with missing download_dir."""
        config = {
            "climate": {
                "source_url": "file://sample.csv",
                "api_key": "test_key",
            },
            "logging": {"level": "INFO"},
        }
        with pytest.raises(KeyError):
            ClimateDownloader(config)


class TestCSVParsing:
    """Test CSV file parsing and data loading."""

    def test_load_csv_with_valid_file(self):
        """Test loading a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "sample.csv"
            csv_path.write_text(
                "station_id,date,element,value\n"
                "ABC123,2024-01-01,TMAX,25.5\n"
                "ABC123,2024-01-01,TMIN,10.2\n"
            )

            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": f"file://{csv_path}",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)
            df = downloader.load_csv(csv_path)

            assert len(df) == 2
            assert list(df.columns) == ["station_id", "date", "element", "value"]

    def test_load_csv_file_not_found(self):
        """Test loading a non-existent CSV file."""
        config = {
            "climate": {
                "download_dir": "data/downloads",
                "source_url": "file://missing.csv",
                "api_key": "test",
            },
            "logging": {"level": "INFO"},
        }
        downloader = ClimateDownloader(config)

        with pytest.raises(FileNotFoundError):
            downloader.load_csv(Path("missing.csv"))

    def test_load_csv_with_missing_values(self):
        """Test loading CSV with missing/null values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "sample.csv"
            csv_path.write_text(
                "station_id,date,element,value\n"
                "ABC123,2024-01-01,TMAX,25.5\n"
                "ABC123,2024-01-01,TMIN,\n"
                "DEF456,2024-01-02,PRCP,\n"
            )

            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": f"file://{csv_path}",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)
            df = downloader.load_csv(csv_path)

            assert len(df) == 3
            assert pd.isna(df.iloc[1]["value"])
            assert pd.isna(df.iloc[2]["value"])

    def test_load_csv_empty_file(self):
        """Test loading an empty CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "empty.csv"
            csv_path.write_text("station_id,date,element,value\n")

            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": f"file://{csv_path}",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)
            df = downloader.load_csv(csv_path)

            assert len(df) == 0


class TestDataValidation:
    """Test data validation and integrity checks."""

    def test_validate_required_columns(self):
        """Test validation of required columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            # Valid dataframe
            df_valid = pd.DataFrame({
                "station_id": ["ABC123"],
                "date": ["2024-01-01"],
                "element": ["TMAX"],
                "value": [25.5],
            })
            assert downloader.validate_columns(df_valid)

            # Invalid dataframe - missing column
            df_invalid = pd.DataFrame({
                "station_id": ["ABC123"],
                "date": ["2024-01-01"],
                "element": ["TMAX"],
            })
            with pytest.raises(ValueError):
                downloader.validate_columns(df_invalid)

    def test_validate_date_format(self):
        """Test validation of date format (YYYY-MM-DD)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            # Valid dates
            df_valid = pd.DataFrame({
                "station_id": ["ABC123", "ABC123"],
                "date": ["2024-01-01", "2024-12-31"],
                "element": ["TMAX", "TMIN"],
                "value": [25.5, 10.2],
            })
            assert downloader.validate_dates(df_valid)

            # Invalid date format
            df_invalid = pd.DataFrame({
                "station_id": ["ABC123"],
                "date": ["01/01/2024"],
                "element": ["TMAX"],
                "value": [25.5],
            })
            with pytest.raises(ValueError):
                downloader.validate_dates(df_invalid)

    def test_validate_element_types(self):
        """Test validation of element types (TMAX, TMIN, PRCP, etc.)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            # Valid elements
            df_valid = pd.DataFrame({
                "station_id": ["ABC123", "ABC123", "ABC123"],
                "date": ["2024-01-01", "2024-01-01", "2024-01-01"],
                "element": ["TMAX", "TMIN", "PRCP"],
                "value": [25.5, 10.2, 5.0],
            })
            assert downloader.validate_elements(df_valid)

            # Invalid element
            df_invalid = pd.DataFrame({
                "station_id": ["ABC123"],
                "date": ["2024-01-01"],
                "element": ["INVALID"],
                "value": [25.5],
            })
            with pytest.raises(ValueError):
                downloader.validate_elements(df_invalid)

    def test_validate_numeric_values(self):
        """Test validation that value column contains numeric data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            # Valid numeric values
            df_valid = pd.DataFrame({
                "station_id": ["ABC123", "ABC123"],
                "date": ["2024-01-01", "2024-01-01"],
                "element": ["TMAX", "TMIN"],
                "value": [25.5, 10.2],
            })
            assert downloader.validate_numeric_values(df_valid)

            # Non-numeric values
            df_invalid = pd.DataFrame({
                "station_id": ["ABC123"],
                "date": ["2024-01-01"],
                "element": ["TMAX"],
                "value": ["invalid"],
            })
            with pytest.raises(ValueError):
                downloader.validate_numeric_values(df_invalid)

    def test_validate_station_ids(self):
        """Test validation that station IDs are present and non-empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            # Valid station IDs
            df_valid = pd.DataFrame({
                "station_id": ["ABC123", "DEF456"],
                "date": ["2024-01-01", "2024-01-01"],
                "element": ["TMAX", "TMIN"],
                "value": [25.5, 10.2],
            })
            assert downloader.validate_station_ids(df_valid)

            # Missing station IDs
            df_invalid = pd.DataFrame({
                "station_id": [None, "ABC123"],
                "date": ["2024-01-01", "2024-01-01"],
                "element": ["TMAX", "TMIN"],
                "value": [25.5, 10.2],
            })
            with pytest.raises(ValueError):
                downloader.validate_station_ids(df_invalid)


class TestDataFiltering:
    """Test data filtering and selection."""

    def test_filter_by_station_ids(self):
        """Test filtering data by specific station IDs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "filtering": {"station_ids": ["ABC123"]},
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            df = pd.DataFrame({
                "station_id": ["ABC123", "ABC123", "DEF456"],
                "date": ["2024-01-01", "2024-01-02", "2024-01-01"],
                "element": ["TMAX", "TMIN", "PRCP"],
                "value": [25.5, 10.2, 5.0],
            })

            filtered = downloader.filter_by_station_ids(df)
            assert len(filtered) == 2
            assert all(filtered["station_id"] == "ABC123")

    def test_filter_by_element_types(self):
        """Test filtering data by specific element types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "filtering": {"data_types": ["TMAX", "TMIN"]},
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            df = pd.DataFrame({
                "station_id": ["ABC123", "ABC123", "ABC123"],
                "date": ["2024-01-01", "2024-01-01", "2024-01-01"],
                "element": ["TMAX", "TMIN", "PRCP"],
                "value": [25.5, 10.2, 5.0],
            })

            filtered = downloader.filter_by_element_types(df)
            assert len(filtered) == 2
            assert all(filtered["element"].isin(["TMAX", "TMIN"]))

    def test_filter_by_date_range(self):
        """Test filtering data by date range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            df = pd.DataFrame({
                "station_id": ["ABC123", "ABC123", "ABC123"],
                "date": ["2024-01-01", "2024-06-15", "2024-12-31"],
                "element": ["TMAX", "TMAX", "TMAX"],
                "value": [25.5, 30.0, 15.0],
            })

            filtered = downloader.filter_by_date_range(
                df, "2024-01-01", "2024-06-30"
            )
            assert len(filtered) == 2


class TestFileOperations:
    """Test file save and retrieval operations."""

    def test_save_csv(self):
        """Test saving dataframe to CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            df = pd.DataFrame({
                "station_id": ["ABC123"],
                "date": ["2024-01-01"],
                "element": ["TMAX"],
                "value": [25.5],
            })

            output_path = Path(tmpdir) / "output.csv"
            downloader.save_csv(df, output_path)

            assert output_path.exists()
            df_loaded = pd.read_csv(output_path)
            assert len(df_loaded) == 1

    def test_save_csv_creates_parent_directory(self):
        """Test that save_csv creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": "file://sample.csv",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            df = pd.DataFrame({
                "station_id": ["ABC123"],
                "date": ["2024-01-01"],
                "element": ["TMAX"],
                "value": [25.5],
            })

            output_path = Path(tmpdir) / "subdir" / "output.csv"
            downloader.save_csv(df, output_path)

            assert output_path.exists()


class TestFullWorkflow:
    """Test complete downloader workflows."""

    def test_full_download_workflow(self):
        """Test complete download and validation workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create sample CSV
            csv_path = Path(tmpdir) / "sample.csv"
            csv_path.write_text(
                "station_id,date,element,value,measurement_flag,quality_flag,source_flag\n"
                "ABC123,2024-01-01,TMAX,25.5,,,\n"
                "ABC123,2024-01-01,TMIN,10.2,,,\n"
                "DEF456,2024-01-01,PRCP,5.0,,,\n"
            )

            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": f"file://{csv_path}",
                    "api_key": "test",
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            # Load and validate
            df = downloader.load_csv(csv_path)
            downloader.validate_columns(df)
            downloader.validate_dates(df)
            downloader.validate_elements(df)
            downloader.validate_numeric_values(df)

            assert len(df) == 3
            assert df["station_id"].nunique() == 2

    def test_download_with_filtering(self):
        """Test download workflow with filtering applied."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "sample.csv"
            csv_path.write_text(
                "station_id,date,element,value,measurement_flag,quality_flag,source_flag\n"
                "ABC123,2024-01-01,TMAX,25.5,,,\n"
                "ABC123,2024-01-01,TMIN,10.2,,,\n"
                "DEF456,2024-01-01,PRCP,5.0,,,\n"
            )

            config = {
                "climate": {
                    "download_dir": tmpdir,
                    "source_url": f"file://{csv_path}",
                    "api_key": "test",
                },
                "filtering": {
                    "station_ids": ["ABC123"],
                    "data_types": ["TMAX", "TMIN"],
                },
                "logging": {"level": "INFO"},
            }
            downloader = ClimateDownloader(config)

            df = downloader.load_csv(csv_path)
            df = downloader.filter_by_station_ids(df)
            df = downloader.filter_by_element_types(df)

            assert len(df) == 2
            assert all(df["station_id"] == "ABC123")
            assert all(df["element"].isin(["TMAX", "TMIN"]))
