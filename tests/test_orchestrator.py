"""End-to-end integration tests for the pipeline orchestrator.

Tests the complete climate data monitoring workflow from data download
through quality assessment to Quilt packaging.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from orchestrator import PipelineOrchestrator


class TestPipelineOrchestrator:
    """Test the complete pipeline orchestration."""

    @pytest.fixture
    def sample_config(self):
        """Create a sample configuration for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            config = {
                "climate": {
                    "source_url": "file://data/sample_climate_data.csv",
                    "api_key": "demo_mode",
                    "download_dir": str(tmpdir_path / "downloads"),
                    "dataset_id": "GHCN_D",
                    "geographic_scope": "test",
                },
                "filtering": {"enabled": False, "station_ids": None, "data_types": None},
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
                    "output_dir": str(tmpdir_path / "quality_reports"),
                },
                "quilt": {
                    "bucket": "test-bucket",
                    "package_name": "climate/test",
                    "registry": "s3://test-bucket",
                    "push_to_registry": False,
                },
                "aws": {"region": "us-west-2", "validate_credentials": False},
                "logging": {"level": "DEBUG", "log_dir": str(tmpdir_path / "logs")},
            }

            # Create necessary directories
            Path(config["climate"]["download_dir"]).mkdir(parents=True, exist_ok=True)
            Path(config["quality"]["output_dir"]).mkdir(parents=True, exist_ok=True)

            yield config

    @pytest.fixture
    def sample_data(self):
        """Create sample climate data for testing."""
        data = {
            "station_id": ["USC00014821", "USC00014821", "USC00023182", "USC00023182"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"],
            "element": ["TMAX", "TMIN", "PRCP", "TMAX"],
            "value": [250, 150, 5, 280],
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def sample_data_file(self, sample_config, sample_data):
        """Write sample data to a file."""
        data_dir = Path(sample_config["climate"]["download_dir"])
        data_dir.mkdir(parents=True, exist_ok=True)

        data_file = data_dir / "test_data.csv"
        sample_data.to_csv(data_file, index=False)
        return data_file

    def test_orchestrator_initialization(self, sample_config):
        """Test that orchestrator initializes with configuration."""
        with patch("orchestrator.ClimateDownloader"):
            with patch("orchestrator.QualityChecker"):
                with patch("orchestrator.QuiltPackager"):
                    orchestrator = PipelineOrchestrator(sample_config, validate_aws=False)

                    assert orchestrator.config == sample_config
                    assert orchestrator.downloader is not None
                    assert orchestrator.quality_checker is not None
                    assert orchestrator.packager is not None
                    assert not orchestrator.aws_validated

    def test_pipeline_run_success(self, sample_config, sample_data_file):
        """Test successful end-to-end pipeline execution."""
        with patch("orchestrator.ClimateDownloader") as MockDownloader:
            with patch("orchestrator.QualityChecker") as MockQuality:
                with patch("orchestrator.QuiltPackager") as MockPackager:
                    # Mock downloader
                    mock_downloader = MagicMock()
                    mock_downloader.load_csv.return_value = pd.DataFrame({
                        "station_id": ["USC00014821"],
                        "date": ["2024-01-01"],
                        "element": ["TMAX"],
                        "value": [250],
                    })
                    mock_downloader.validate_columns.return_value = True
                    mock_downloader.validate_dates.return_value = True
                    mock_downloader.validate_elements.return_value = True
                    mock_downloader.validate_values.return_value = True
                    mock_downloader.validate_station_ids.return_value = True
                    MockDownloader.return_value = mock_downloader

                    # Mock quality checker
                    mock_quality = MagicMock()
                    mock_quality.generate_quality_report.return_value = {
                        "timestamp": "2024-01-01T00:00:00",
                        "row_count": 100,
                        "column_count": 4,
                        "quality_score": 85.5,
                        "null_percentage_avg": 2.5,
                        "duplicate_count": 0,
                        "station_count": 5,
                    }
                    mock_quality.output_dir = Path(sample_config["quality"]["output_dir"])
                    MockQuality.return_value = mock_quality

                    # Mock packager
                    mock_packager = MagicMock()
                    mock_packager.package_name = "climate/test"
                    mock_packager.push_enabled = False
                    mock_packager.full_package_workflow.return_value = True
                    MockPackager.return_value = mock_packager

                    # Run pipeline
                    orchestrator = PipelineOrchestrator(sample_config, validate_aws=False)
                    results = orchestrator.run(sample_data_file)

                    # Verify results
                    assert results["success"] is True
                    assert results["package_name"] == "climate/test"
                    assert results["quality_report"]["quality_score"] == 85.5
                    assert len(results["errors"]) == 0

    def test_pipeline_run_with_filtering(self, sample_config, sample_data_file):
        """Test pipeline with data filtering enabled."""
        sample_config["filtering"]["enabled"] = True
        sample_config["filtering"]["station_ids"] = ["USC00014821"]

        with patch("orchestrator.ClimateDownloader") as MockDownloader:
            with patch("orchestrator.QualityChecker") as MockQuality:
                with patch("orchestrator.QuiltPackager") as MockPackager:
                    mock_downloader = MagicMock()
                    mock_downloader.load_csv.return_value = pd.DataFrame({
                        "station_id": ["USC00014821"],
                        "date": ["2024-01-01"],
                        "element": ["TMAX"],
                        "value": [250],
                    })
                    mock_downloader.validate_columns.return_value = True
                    mock_downloader.validate_dates.return_value = True
                    mock_downloader.validate_elements.return_value = True
                    mock_downloader.validate_values.return_value = True
                    mock_downloader.validate_station_ids.return_value = True
                    mock_downloader.filter_by_station_ids.return_value = pd.DataFrame({
                        "station_id": ["USC00014821"],
                        "date": ["2024-01-01"],
                        "element": ["TMAX"],
                        "value": [250],
                    })
                    MockDownloader.return_value = mock_downloader

                    mock_quality = MagicMock()
                    mock_quality.generate_quality_report.return_value = {
                        "timestamp": "2024-01-01T00:00:00",
                        "row_count": 50,
                        "column_count": 4,
                        "quality_score": 90.0,
                        "null_percentage_avg": 1.0,
                        "duplicate_count": 0,
                        "station_count": 1,
                    }
                    mock_quality.output_dir = Path(sample_config["quality"]["output_dir"])
                    MockQuality.return_value = mock_quality

                    mock_packager = MagicMock()
                    mock_packager.package_name = "climate/test"
                    mock_packager.push_enabled = False
                    mock_packager.full_package_workflow.return_value = True
                    MockPackager.return_value = mock_packager

                    orchestrator = PipelineOrchestrator(sample_config, validate_aws=False)
                    results = orchestrator.run(sample_data_file)

                    # Verify filtering was applied
                    mock_downloader.filter_by_station_ids.assert_called_once()
                    assert results["success"] is True
                    assert results["quality_report"]["station_count"] == 1

    def test_pipeline_handles_errors(self, sample_config):
        """Test that pipeline handles errors gracefully."""
        with patch("orchestrator.ClimateDownloader") as MockDownloader:
            # Mock downloader to raise an error
            MockDownloader.side_effect = ValueError("Invalid configuration")

            orchestrator = PipelineOrchestrator(sample_config, validate_aws=False)
            results = orchestrator.run(Path("nonexistent.csv"))

            assert results["success"] is False
            assert len(results["errors"]) > 0

    def test_status_report_generation(self, sample_config):
        """Test generation of status report."""
        with patch("orchestrator.ClimateDownloader"):
            with patch("orchestrator.QualityChecker"):
                with patch("orchestrator.QuiltPackager"):
                    orchestrator = PipelineOrchestrator(sample_config, validate_aws=False)

                    results = {
                        "success": True,
                        "data_file": "/path/to/data.csv",
                        "quality_report": {
                            "quality_score": 85.5,
                            "row_count": 100,
                            "null_percentage_avg": 2.5,
                            "station_count": 5,
                        },
                        "package_name": "climate/test",
                        "timestamp": "2024-01-01T00:00:00",
                        "errors": [],
                    }

                    report = orchestrator.get_status_report(results)

                    assert "✓ SUCCESS" in report
                    assert "climate/test" in report
                    assert "85.5" in report
                    assert "100" in report

    def test_status_report_with_errors(self, sample_config):
        """Test status report with errors."""
        with patch("orchestrator.ClimateDownloader"):
            with patch("orchestrator.QualityChecker"):
                with patch("orchestrator.QuiltPackager"):
                    orchestrator = PipelineOrchestrator(sample_config, validate_aws=False)

                    results = {
                        "success": False,
                        "data_file": None,
                        "quality_report": None,
                        "package_name": "climate/test",
                        "timestamp": "2024-01-01T00:00:00",
                        "errors": ["Data validation failed", "Invalid station ID"],
                    }

                    report = orchestrator.get_status_report(results)

                    assert "✗ FAILED" in report
                    assert "Data validation failed" in report
                    assert "Invalid station ID" in report

    def test_get_output_filename(self, sample_config):
        """Test output filename generation."""
        with patch("orchestrator.ClimateDownloader"):
            with patch("orchestrator.QualityChecker"):
                with patch("orchestrator.QuiltPackager"):
                    orchestrator = PipelineOrchestrator(sample_config, validate_aws=False)

                    output_file = orchestrator._get_output_filename()

                    assert output_file.name.startswith("climate_data_processed_")
                    assert output_file.suffix == ".csv"
                    assert output_file.parent.name == "downloads"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
