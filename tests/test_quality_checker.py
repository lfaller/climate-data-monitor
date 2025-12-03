"""Tests for QualityChecker module.

Tests cover:
- Data completeness metrics
- Temperature statistics and validation
- Precipitation statistics and validation
- Geographic coverage analysis
- Quality scoring
- Drift detection
- Report generation
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from src.quality_checker import QualityChecker


class TestQualityCheckerInitialization:
    """Test QualityChecker initialization and configuration."""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output/quality_reports",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)
        assert checker.config == config
        assert checker.min_quality_score == 75

    def test_init_creates_output_directory(self):
        """Test that initialization creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "quality": {
                    "thresholds": {
                        "min_quality_score": 75,
                        "max_null_percentage": 15,
                        "max_outlier_percentage": 5,
                        "temp_outlier_std_dev": 3,
                        "temp_min_valid": -60,
                        "temp_max_valid": 60,
                        "precip_max_daily": 500,
                    },
                    "output_dir": tmpdir + "/reports",
                },
                "logging": {"level": "INFO"},
            }
            checker = QualityChecker(config)
            assert checker.output_dir.exists()


class TestDataCompletenessMetrics:
    """Test data completeness calculation."""

    def test_calculate_null_percentage(self):
        """Test null value percentage calculation."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df = pd.DataFrame({
            "station_id": ["A", "A", "A", "A"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "element": ["TMAX", "TMAX", "TMAX", "TMAX"],
            "value": [25.5, None, 28.0, 26.5],
        })

        null_pct = checker.calculate_null_percentage(df)
        assert null_pct == 25.0

    def test_calculate_null_percentage_no_nulls(self):
        """Test null percentage when no nulls present."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df = pd.DataFrame({
            "station_id": ["A", "A", "A"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "element": ["TMAX", "TMAX", "TMAX"],
            "value": [25.5, 28.0, 26.5],
        })

        null_pct = checker.calculate_null_percentage(df)
        assert null_pct == 0.0

    def test_count_duplicates(self):
        """Test duplicate record detection."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df = pd.DataFrame({
            "station_id": ["A", "A", "A", "B"],
            "date": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-01"],
            "element": ["TMAX", "TMAX", "TMAX", "TMAX"],
            "value": [25.5, 25.5, 28.0, 26.5],
        })

        dup_count = checker.count_duplicates(df)
        assert dup_count == 1


class TestTemperatureMetrics:
    """Test temperature-specific quality metrics."""

    def test_calculate_temperature_statistics(self):
        """Test calculation of temperature min/max/mean."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df = pd.DataFrame({
            "station_id": ["A", "A", "A"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "element": ["TMAX", "TMAX", "TMAX"],
            "value": [20.0, 25.0, 30.0],
        })

        stats = checker.calculate_temperature_statistics(df)
        assert stats["tmax_min"] == 20.0
        assert stats["tmax_max"] == 30.0
        assert stats["tmax_mean"] == 25.0

    def test_detect_temperature_outliers(self):
        """Test detection of temperature outliers (>3 std dev)."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        # Create data with clear outlier (very extreme value)
        df = pd.DataFrame({
            "station_id": ["A"] * 11,
            "date": [f"2024-01-{i:02d}" for i in range(1, 12)],
            "element": ["TMAX"] * 11,
            "value": [20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 200.0],
        })

        outlier_count = checker.detect_temperature_outliers(df)
        assert outlier_count >= 1

    def test_validate_temperature_range(self):
        """Test validation that temperatures are within valid range."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        # Valid temperatures
        df_valid = pd.DataFrame({
            "station_id": ["A", "A"],
            "date": ["2024-01-01", "2024-01-02"],
            "element": ["TMAX", "TMAX"],
            "value": [25.0, -10.0],
        })
        assert checker.validate_temperature_range(df_valid) is True

        # Invalid temperatures
        df_invalid = pd.DataFrame({
            "station_id": ["A", "A"],
            "date": ["2024-01-01", "2024-01-02"],
            "element": ["TMAX", "TMAX"],
            "value": [25.0, 100.0],
        })
        with pytest.raises(ValueError):
            checker.validate_temperature_range(df_invalid)

    def test_missing_days_detection(self):
        """Test detection of missing days for stations."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df = pd.DataFrame({
            "station_id": ["A", "A", "A"],
            "date": ["2024-01-01", "2024-01-03", "2024-01-05"],
            "element": ["TMAX", "TMAX", "TMAX"],
            "value": [20.0, 25.0, 30.0],
        })

        missing_days = checker.detect_missing_days(df, "2024-01-01", "2024-01-05")
        assert missing_days >= 2


class TestPrecipitationMetrics:
    """Test precipitation-specific quality metrics."""

    def test_calculate_precipitation_statistics(self):
        """Test calculation of precipitation stats."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df = pd.DataFrame({
            "station_id": ["A", "A", "A"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "element": ["PRCP", "PRCP", "PRCP"],
            "value": [0.0, 5.0, 10.0],
        })

        stats = checker.calculate_precipitation_statistics(df)
        assert stats["prcp_min"] == 0.0
        assert stats["prcp_max"] == 10.0
        assert stats["prcp_mean"] == 5.0

    def test_zero_precipitation_percentage(self):
        """Test calculation of days with zero precipitation (normal)."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df = pd.DataFrame({
            "station_id": ["A", "A", "A", "A"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "element": ["PRCP", "PRCP", "PRCP", "PRCP"],
            "value": [0.0, 0.0, 5.0, 0.0],
        })

        zero_pct = checker.calculate_zero_precipitation_percentage(df)
        assert zero_pct == 75.0

    def test_detect_precipitation_extremes(self):
        """Test detection of extreme precipitation values."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df = pd.DataFrame({
            "station_id": ["A", "A", "A"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "element": ["PRCP", "PRCP", "PRCP"],
            "value": [5.0, 10.0, 600.0],
        })

        extreme_count = checker.detect_precipitation_extremes(df)
        assert extreme_count > 0


class TestGeographicCoverage:
    """Test geographic coverage analysis."""

    def test_count_active_stations(self):
        """Test counting of active reporting stations."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df = pd.DataFrame({
            "station_id": ["A", "A", "B", "B", "C"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02", "2024-01-01"],
            "element": ["TMAX", "TMAX", "TMAX", "TMAX", "TMAX"],
            "value": [20.0, 21.0, 22.0, 23.0, 24.0],
        })

        active_count = checker.count_active_stations(df)
        assert active_count == 3

    def test_detect_new_stations(self):
        """Test detection of newly reporting stations."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df_current = pd.DataFrame({
            "station_id": ["A", "B", "C"],
            "date": ["2024-01-01", "2024-01-01", "2024-01-01"],
            "element": ["TMAX", "TMAX", "TMAX"],
            "value": [20.0, 21.0, 22.0],
        })

        df_previous = pd.DataFrame({
            "station_id": ["A", "B"],
            "date": ["2023-12-31", "2023-12-31"],
            "element": ["TMAX", "TMAX"],
            "value": [20.0, 21.0],
        })

        new_stations = checker.detect_new_stations(df_current, df_previous)
        assert "C" in new_stations

    def test_detect_inactive_stations(self):
        """Test detection of stations that stopped reporting."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        df_current = pd.DataFrame({
            "station_id": ["A", "B"],
            "date": ["2024-01-01", "2024-01-01"],
            "element": ["TMAX", "TMAX"],
            "value": [20.0, 21.0],
        })

        df_previous = pd.DataFrame({
            "station_id": ["A", "B", "C"],
            "date": ["2023-12-31", "2023-12-31", "2023-12-31"],
            "element": ["TMAX", "TMAX", "TMAX"],
            "value": [20.0, 21.0, 22.0],
        })

        inactive_stations = checker.detect_inactive_stations(df_current, df_previous)
        assert "C" in inactive_stations


class TestQualityScoring:
    """Test overall quality score calculation."""

    def test_calculate_quality_score(self):
        """Test calculation of overall quality score."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        # Perfect data
        df = pd.DataFrame({
            "station_id": ["A", "A", "A"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "element": ["TMAX", "TMAX", "TMAX"],
            "value": [20.0, 21.0, 22.0],
        })

        score = checker.calculate_quality_score(df)
        assert 0 <= score <= 100
        assert score > 70

    def test_quality_score_with_missing_data(self):
        """Test quality score decreases with missing data."""
        config = {
            "quality": {
                "thresholds": {
                    "min_quality_score": 75,
                    "max_null_percentage": 15,
                    "max_outlier_percentage": 5,
                    "temp_outlier_std_dev": 3,
                    "temp_min_valid": -60,
                    "temp_max_valid": 60,
                    "precip_max_daily": 500,
                },
                "output_dir": "output",
            },
            "logging": {"level": "INFO"},
        }
        checker = QualityChecker(config)

        # Data with 30% nulls
        df = pd.DataFrame({
            "station_id": ["A"] * 10,
            "date": [f"2024-01-{i:02d}" for i in range(1, 11)],
            "element": ["TMAX"] * 10,
            "value": [20.0, None, 21.0, None, 22.0, None, 23.0, None, 24.0, None],
        })

        score = checker.calculate_quality_score(df)
        assert score < 80


class TestReportGeneration:
    """Test quality report generation."""

    def test_generate_quality_report(self):
        """Test generation of complete quality report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "quality": {
                    "thresholds": {
                        "min_quality_score": 75,
                        "max_null_percentage": 15,
                        "max_outlier_percentage": 5,
                        "temp_outlier_std_dev": 3,
                        "temp_min_valid": -60,
                        "temp_max_valid": 60,
                        "precip_max_daily": 500,
                    },
                    "output_dir": tmpdir,
                },
                "logging": {"level": "INFO"},
            }
            checker = QualityChecker(config)

            df = pd.DataFrame({
                "station_id": ["A", "A", "A"],
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "element": ["TMAX", "TMAX", "TMAX"],
                "value": [20.0, 21.0, 22.0],
            })

            report = checker.generate_quality_report(df)

            assert "timestamp" in report
            assert "quality_score" in report
            assert "row_count" in report
            assert "null_percentage_avg" in report
            assert "temperature_range" in report

    def test_save_quality_report(self):
        """Test saving quality report to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "quality": {
                    "thresholds": {
                        "min_quality_score": 75,
                        "max_null_percentage": 15,
                        "max_outlier_percentage": 5,
                        "temp_outlier_std_dev": 3,
                        "temp_min_valid": -60,
                        "temp_max_valid": 60,
                        "precip_max_daily": 500,
                    },
                    "output_dir": tmpdir,
                },
                "logging": {"level": "INFO"},
            }
            checker = QualityChecker(config)

            df = pd.DataFrame({
                "station_id": ["A", "A", "A"],
                "date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "element": ["TMAX", "TMAX", "TMAX"],
                "value": [20.0, 21.0, 22.0],
            })

            report = checker.generate_quality_report(df)
            report_path = checker.save_quality_report(report)

            assert report_path.exists()
            assert report_path.suffix == ".json"


class TestFullWorkflow:
    """Test complete quality checking workflow."""

    def test_full_quality_check_workflow(self):
        """Test complete quality assessment workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "quality": {
                    "thresholds": {
                        "min_quality_score": 75,
                        "max_null_percentage": 15,
                        "max_outlier_percentage": 5,
                        "temp_outlier_std_dev": 3,
                        "temp_min_valid": -60,
                        "temp_max_valid": 60,
                        "precip_max_daily": 500,
                    },
                    "output_dir": tmpdir,
                },
                "logging": {"level": "INFO"},
            }
            checker = QualityChecker(config)

            df = pd.DataFrame({
                "station_id": ["A", "A", "B", "B"],
                "date": ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"],
                "element": ["TMAX", "TMAX", "TMIN", "TMIN"],
                "value": [20.0, 21.0, 5.0, 6.0],
            })

            report = checker.assess_quality(df)

            assert "timestamp" in report
            assert "quality_score" in report
            assert report["row_count"] == 4
            assert report["station_count"] == 2
