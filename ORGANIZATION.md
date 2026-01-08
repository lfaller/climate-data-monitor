# Project Organization

This document describes how the climate-data-monitor project is organized.

## Directory Structure

```
climate-data-monitor/
├── src/                          # Source code
│   ├── __main__.py              # CLI entry point
│   ├── orchestrator.py          # Pipeline orchestration
│   ├── downloader.py            # Data ingestion
│   ├── quality_checker.py       # Quality assessment
│   └── quilt_packager.py        # Quilt integration
│
├── tests/                        # Test suite (61+ tests)
│   ├── test_downloader.py       # 20 tests
│   ├── test_quality_checker.py  # 20+ tests
│   ├── test_quilt_packager.py   # 21 tests
│   └── test_orchestrator.py     # 14 integration tests
│
├── config/                       # Configuration
│   ├── demo_config.yaml         # Local testing config
│   ├── production_config.yaml.template  # AWS S3 template
│   └── aws_setup.py             # AWS utilities
│
├── data/                         # Data storage
│   ├── sample_climate_data.csv  # Test fixture
│   └── downloads/               # Downloaded data
│
├── docs/                         # Public documentation
│   ├── README.md                # Documentation index
│   ├── PIPELINE_GUIDE.md        # Complete usage guide
│   ├── IMPLEMENTATION_SUMMARY.md # Technical details
│   ├── DELIVERY_SUMMARY.md      # Project delivery
│   ├── PROJECT_PLAN.md          # Roadmap
│   └── CHANGELOG.md             # Version history
│
├── local/                        # Local-only files (not tracked)
│
├── output/                       # Generated output
│   └── quality_reports/         # Quality report JSONs
│
├── logs/                         # Pipeline logs
│
├── README.md                     # Project overview
├── ORGANIZATION.md               # This file
├── QUICK_REFERENCE.md           # Quick navigation guide
├── MIGRATION_CHECKLIST.md       # Project setup record
├── .gitignore                    # Git exclusions
└── pyproject.toml                # Poetry configuration
```

## Folder Details

### `/src` - Source Code
All application code:
- **orchestrator.py** - Coordinates the complete pipeline workflow
- **__main__.py** - CLI entry point for running the pipeline
- **downloader.py** - NOAA data ingestion and validation
- **quality_checker.py** - Quality metrics calculation
- **quilt_packager.py** - Quilt integration and S3 registry access

### `/tests` - Test Suite
Comprehensive tests (61+ total):
- **test_downloader.py** - 20 tests for data validation
- **test_quality_checker.py** - 20+ tests for metrics
- **test_quilt_packager.py** - 21 tests for packaging
- **test_orchestrator.py** - 14 integration tests

Test-to-code ratio: 1.54:1 (excellent coverage)

### `/config` - Configuration
Configuration files and AWS utilities:
- **demo_config.yaml** - Pre-configured for local testing
- **production_config.yaml.template** - Template for AWS S3 deployment
- **aws_setup.py** - AWS credential validation utilities

### `/docs` - Documentation
Public documentation for users and developers:
- **PIPELINE_GUIDE.md** - How to run the pipeline
- **IMPLEMENTATION_SUMMARY.md** - Technical architecture
- **DELIVERY_SUMMARY.md** - What was delivered
- **PROJECT_PLAN.md** - Future roadmap

### `/local` - Local-Only Files
This folder is excluded from git and contains local development files. Create what you need here without worrying about version control.

```bash
# Files in /local are never committed
git check-ignore local/  # Returns: local/
```

## How to Use This Organization

### If you're a user of the project:
1. Read [README.md](README.md) for overview
2. Go to [docs/](docs/) for documentation
3. Follow [docs/PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md)

### If you're contributing code:
1. Review [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) for architecture
2. Check [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) for what's next
3. Look at code in `src/` and tests in `tests/`

### If you're developing locally:
1. Use `/local/` for any temporary files
2. They won't be tracked by git
3. Perfect for development notes, test data, etc.

## Key Principles

1. **Clean separation** - Source, tests, docs, and config are clearly organized
2. **Public by default** - Everything in the repo is public except `/local/`
3. **Well documented** - All public docs in `/docs/` with clear navigation
4. **Easy to understand** - Clear folder purposes and naming conventions
5. **Test-driven** - Tests alongside code with high coverage

## Git Tracking

- ✅ Tracked: Everything except `/local/`
- ❌ Not tracked: `/local/` (see `.gitignore`)

All other files are part of the public repository and safe to commit.

## File Changes

To see what changed during project reorganization, refer to [MIGRATION_CHECKLIST.md](MIGRATION_CHECKLIST.md).
