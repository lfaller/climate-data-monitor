# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ClimateDownloader module for fetching NOAA climate data
- QualityChecker module with climate-specific metrics
- Comprehensive test suite (80+ tests)
- Demo pipeline for testing with sample data
- End-to-end pipeline orchestration

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
