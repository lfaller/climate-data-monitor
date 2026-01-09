# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-01-09

### Added

#### Real Weather Data Integration
- Integrated Open-Meteo API for free historical weather data (no API keys needed)
- Added `fetch_open_meteo_data.py` helper script to download real climate data
- NYC weather data (2023-2025): 1,095-1,098 records per year, 0% null values
- Real data exploration documentation: `explore_real_data_sources.py`

#### Quality Score Redesign
- Replaced geographic coverage metric with actionable metrics
- New 5-metric quality scoring system:
  * Data Completeness: 30 points (null % check)
  * Outlier Rate: 25 points (impossible temperature values)
  * Temporal Completeness: 20 points (date range coverage)
  * Seasonality Confidence: 15 points (seasonal pattern detection)
  * Schema Stability: 10 points (required columns present)
- NYC data now scores 99.3-100/100 (previously 77/100)
- Scores now accurately reflect single-location data quality

#### Model Context Protocol (MCP) Integration
- Implemented `MCPClimateAnalyzer` with 7 query types:
  * `search()` - Find packages by quality/elements
  * `metrics()` - Extract quality metrics
  * `temperature()` - Analyze temperature patterns
  * `completeness()` - Check data completeness by element/station
  * `compare()` - Drift detection between versions
  * `sample()` - Fetch sample data for AI context
  * `report()` - Generate human-readable summaries
- CLI commands for MCP queries: `python -m src mcp <query_type>`
- Interactive demos showing Claude autonomous analysis capabilities
- Full MCP integration documentation

#### Data Schema Simplification
- Removed empty `measurement_flag` and `quality_flag` columns
- Simplified schema: station_id, date, element, value, source_flag (5 columns)
- Result: 0% null percentage reporting (previously 28.57%)
- Cleaner, more honest data quality metrics

#### Bug Fixes
- Fixed null_percentage calculation in data completeness analysis
- Corrected denominator to use (rows × columns) instead of just rows
- Percentages now correctly range 0-100% (previously could exceed 100%)

### Changed
- Documentation updated to reflect Open-Meteo as primary data source
- All quality metrics and examples updated with new 5-metric scoring
- Architecture diagrams updated to include MCP analyzer layer
- Project status: Phase 1 Complete, Phase 2 In Progress (MCP)

## [0.3.0] - 2025-12-02

### Added

#### QuiltPackager Test Suite
- 21 comprehensive tests for Quilt package creation and S3 integration
- Tests cover:
  * Package initialization and configuration
  * Package creation with and without data files
  * Data file validation (existence, type, permissions)
  * Metadata attachment and validation
  * Quality report integration
  * S3 registry operations (push/build modes)
  * Complete end-to-end workflows
- Mocked Quilt3 API (no AWS credentials needed for tests)
- Both local build and S3 push modes tested
- Comprehensive error handling tests

### Status
- Phase 1: Pipeline Foundation - Tests Ready ✅
- 61/80+ tests passing
- Ready for pipeline orchestration implementation

## [0.2.0] - 2025-12-02

### Added

#### Phase 1: Foundation Complete

**ClimateDownloader Module**
- Load and parse NOAA climate data from CSV files
- Comprehensive 5-step data validation pipeline:
  * Required columns validation (station_id, date, element, value)
  * Date format validation (YYYY-MM-DD)
  * Element type validation (TMAX, TMIN, PRCP, SNOW, SNWD, etc.)
  * Numeric value validation
  * Station ID presence validation
- Flexible filtering capabilities:
  * Filter by specific station IDs
  * Filter by element types (temperature, precipitation, snow)
  * Filter by date range
- File operations (load, save, validate)
- Complete workflow: `download_and_validate()`

**QualityChecker Module**
- Data completeness metrics:
  * Null percentage calculation
  * Duplicate record detection
- Temperature-specific metrics:
  * Min/max/mean statistics
  * Outlier detection (>3 std dev)
  * Valid range validation
  * Missing day detection
- Precipitation-specific metrics:
  * Min/max/mean statistics
  * Zero precipitation percentage
  * Extreme value detection (>500mm/day)
- Geographic coverage analysis:
  * Active station counting
  * New station detection
  * Inactive station detection
- Quality scoring (0-100 scale):
  * Completeness: 30 points
  * Outlier rate: 25 points
  * Temperature range validity: 10 points
  * Geographic coverage: 25 points
  * Schema stability: 10 points
- Quality report generation and JSON export

**Testing & Quality**
- 40 comprehensive tests (20 ClimateDownloader + 20 QualityChecker)
- 100% test pass rate
- TDD approach: tests written before implementation
- Real NOAA GHCN-Daily data structure support

### Status
- Phase 1: Foundation - COMPLETE ✅
- 40/80+ tests passing
- Ready for pipeline orchestration and demo pipeline

## [0.1.0] - 2025-11-24

### Added

#### Project Setup
- Initial project structure with Poetry configuration
- Reusable QuiltPackager module from ClinVar reference project
- Configuration templates for NOAA climate data (NCEI Monthly Summaries)
- Environment configuration template (.env.template)

#### Sample Data
- Real NOAA GHCN-Daily sample data (200 records from January 1, 2024)
- Multiple weather stations with temperature, precipitation, and snow measurements
- Demo configuration for local testing

#### Documentation
- PROJECT_PLAN.md with comprehensive 3-phase implementation roadmap
- Phase 1 focus: Basic working pipeline with climate data

### Status
- Phase 1: Foundation - In Progress
- Project initialized and foundational files committed to GitHub
