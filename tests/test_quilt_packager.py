"""Tests for QuiltPackager module.

Tests cover:
- Package initialization and configuration
- Data file handling
- Metadata attachment
- Quality report integration
- Local building and S3 pushing
- Validation and error handling
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest

from src.quilt_packager import QuiltPackager


class TestQuiltPackagerInitialization:
    """Test QuiltPackager initialization and configuration."""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test-data",
                "registry": "s3://test-bucket",
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        assert packager.bucket == "test-bucket"
        assert packager.package_name == "climate/test-data"
        assert packager.registry == "s3://test-bucket"
        assert packager.push_enabled is True  # Auto-detected from s3:// URL

    def test_init_parses_package_name(self):
        """Test that package name is correctly parsed into namespace/package."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/noaa-monthly",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        assert packager.namespace == "climate"
        assert packager.package == "noaa-monthly"
        assert packager.package_name == "climate/noaa-monthly"

    def test_init_with_missing_quilt_config(self):
        """Test initialization fails with missing quilt config."""
        config = {"logging": {"level": "INFO"}}

        with pytest.raises(KeyError):
            QuiltPackager(config)

    def test_init_with_default_namespace(self):
        """Test that default namespace is used if not in package name."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "test-package",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        assert packager.namespace == "climate"
        assert packager.package == "test-package"


class TestPackageCreation:
    """Test Quilt package creation."""

    @patch("src.quilt_packager.quilt3.Package")
    def test_create_package(self, mock_package_class):
        """Test creating a new Quilt package."""
        mock_pkg = Mock()
        mock_package_class.return_value = mock_pkg

        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        pkg = packager.create_package()

        assert pkg == mock_pkg
        mock_package_class.assert_called_once()

    @patch("src.quilt_packager.quilt3.Package")
    def test_create_package_with_data_file(self, mock_package_class):
        """Test creating a package with initial data file."""
        mock_pkg = Mock()
        mock_package_class.return_value = mock_pkg

        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "data.csv"
            data_file.write_text("station,date,value\nA,2024-01-01,25.5")

            pkg = packager.create_package(data_file)

            assert pkg == mock_pkg
            mock_pkg.set.assert_called_once()


class TestDataFileHandling:
    """Test data file operations."""

    @patch("src.quilt_packager.quilt3.Package")
    def test_add_data_file(self, mock_package_class):
        """Test adding data file to package."""
        mock_pkg = Mock()

        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "data.csv"
            data_file.write_text("station,date,value\nA,2024-01-01,25.5")

            result = packager.add_data_file(mock_pkg, data_file)

            assert result == mock_pkg
            mock_pkg.set.assert_called_once_with("data.csv", data_file)

    def test_add_data_file_not_found(self):
        """Test adding non-existent data file raises error."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)
        mock_pkg = Mock()

        with pytest.raises(FileNotFoundError):
            packager.add_data_file(mock_pkg, Path("nonexistent.csv"))

    def test_validate_data_file_exists(self):
        """Test validation of existing data file."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "data.csv"
            data_file.write_text("station,date,value\nA,2024-01-01,25.5")

            assert packager.validate_data_file(data_file) is True

    def test_validate_data_file_not_found(self):
        """Test validation fails for missing file."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        with pytest.raises(FileNotFoundError):
            packager.validate_data_file(Path("nonexistent.csv"))

    def test_validate_data_file_is_directory(self):
        """Test validation fails if path is directory."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                packager.validate_data_file(Path(tmpdir))


class TestMetadataHandling:
    """Test metadata attachment and validation."""

    @patch("src.quilt_packager.quilt3.Package")
    def test_add_quality_report(self, mock_package_class):
        """Test adding quality report as metadata."""
        mock_pkg = Mock()

        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        quality_report = {
            "timestamp": "2024-01-01T00:00:00",
            "row_count": 100,
            "column_count": 4,
            "quality_score": 85.0,
            "null_percentage_avg": 2.5,
            "duplicate_count": 0,
            "station_count": 5,
        }

        result = packager.add_quality_report(mock_pkg, quality_report)

        assert result == mock_pkg
        mock_pkg.set_meta.assert_called_once()

    def test_validate_quality_report(self):
        """Test validation of quality report."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        # Valid report
        valid_report = {
            "timestamp": "2024-01-01T00:00:00",
            "row_count": 100,
            "column_count": 4,
            "quality_score": 85.0,
        }
        assert packager.validate_quality_report(valid_report) is True

        # Missing required field
        invalid_report = {
            "timestamp": "2024-01-01T00:00:00",
            "row_count": 100,
        }
        with pytest.raises(ValueError):
            packager.validate_quality_report(invalid_report)

    @patch("src.quilt_packager.quilt3.Package")
    def test_set_metadata(self, mock_package_class):
        """Test setting custom metadata."""
        mock_pkg = Mock()

        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        metadata = {
            "version": "0.2.0",
            "dataset": "NOAA GHCN-Daily",
        }

        result = packager.set_metadata(mock_pkg, metadata)

        assert result == mock_pkg
        mock_pkg.set_meta.assert_called_once_with(metadata)


class TestRegistryOperations:
    """Test S3 registry operations."""

    @patch("src.quilt_packager.quilt3.Package")
    def test_push_to_registry_disabled(self, mock_package_class):
        """Test building package locally with local registry."""
        mock_pkg = Mock()

        config = {
            "quilt": {
                "package_name": "climate/test",
                "registry": "local",
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        result = packager.push_to_registry(mock_pkg)

        assert result is True
        mock_pkg.build.assert_called_once()

    @patch("src.quilt_packager.quilt3.Package")
    def test_push_to_registry_enabled(self, mock_package_class):
        """Test pushing to S3 registry when enabled."""
        mock_pkg = Mock()

        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": True,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        result = packager.push_to_registry(mock_pkg)

        assert result is True
        mock_pkg.push.assert_called_once()

    @patch("src.quilt_packager.quilt3.list_packages")
    def test_get_registry_packages(self, mock_list_packages):
        """Test retrieving package list from registry."""
        mock_packages = [
            {"name": "climate/test1", "hash": "hash1"},
            {"name": "climate/test2", "hash": "hash2"},
        ]
        mock_list_packages.return_value = mock_packages

        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        packages = packager.get_registry_packages()

        assert len(packages) == 2
        assert packages[0]["name"] == "climate/test1"


class TestMetadataGeneration:
    """Test metadata generation from quality reports."""

    def test_generate_metadata_from_report(self):
        """Test metadata generation from quality report."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        report = {
            "timestamp": "2024-01-01T12:00:00",
            "quality_score": 87.5,
            "row_count": 1000,
            "column_count": 7,
            "null_percentage_avg": 1.2,
            "duplicate_count": 2,
            "temperature_range": {"tmax_mean": 22.5},
            "precipitation_stats": {"prcp_max": 25.0},
            "station_count": 10,
        }

        metadata = packager._generate_metadata_from_report(report)

        assert metadata["timestamp"] == "2024-01-01T12:00:00"
        assert metadata["quality_score"] == 87.5
        assert metadata["row_count"] == 1000
        assert metadata["station_count"] == 10


class TestCompleteWorkflow:
    """Test complete packaging workflow."""

    @patch("src.quilt_packager.quilt3.Package")
    def test_full_package_workflow(self, mock_package_class):
        """Test complete package workflow with local registry."""
        mock_pkg = Mock()
        mock_package_class.return_value = mock_pkg

        config = {
            "quilt": {
                "package_name": "climate/test",
                "registry": "local",
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "data.csv"
            data_file.write_text("station,date,value\nA,2024-01-01,25.5")

            quality_report = {
                "timestamp": "2024-01-01T00:00:00",
                "row_count": 1,
                "column_count": 3,
                "quality_score": 90.0,
            }

            result = packager.full_package_workflow(data_file, quality_report)

            assert result is True
            mock_package_class.assert_called()
            mock_pkg.set.assert_called()
            mock_pkg.set_meta.assert_called()
            mock_pkg.build.assert_called()

    @patch("src.quilt_packager.quilt3.Package")
    def test_full_workflow_with_invalid_file(self, mock_package_class):
        """Test workflow fails with invalid data file."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        quality_report = {
            "timestamp": "2024-01-01T00:00:00",
            "row_count": 1,
            "column_count": 3,
            "quality_score": 90.0,
        }

        with pytest.raises(FileNotFoundError):
            packager.full_package_workflow(Path("nonexistent.csv"), quality_report)

    @patch("src.quilt_packager.quilt3.Package")
    def test_full_workflow_with_invalid_report(self, mock_package_class):
        """Test workflow fails with invalid quality report."""
        config = {
            "quilt": {
                "bucket": "test-bucket",
                "package_name": "climate/test",
                "registry": "s3://test-bucket",
                "push_to_registry": False,
            },
            "logging": {"level": "INFO"},
        }
        packager = QuiltPackager(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "data.csv"
            data_file.write_text("station,date,value\nA,2024-01-01,25.5")

            invalid_report = {
                "timestamp": "2024-01-01T00:00:00",
            }

            with pytest.raises(ValueError):
                packager.full_package_workflow(data_file, invalid_report)
