# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
