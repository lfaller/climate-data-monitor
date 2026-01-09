# Climate Data Quality Monitor - Project Plan

**Project Status:** NEW - Starting Implementation
**Based on:** ClinVar Data Quality Monitor architecture (archived reference project)
**Start Date:** November 24, 2025

---

## Executive Summary

Build an automated data quality monitoring system for real climate data using Quilt for versioning and Model Context Protocol (MCP) for AI-assisted analysis. This project applies the proven architecture from the ClinVar project to real-world weather data with modern AI capabilities.

**Why This Approach?**
- **Real Data:** Open-Meteo API provides free, global historical weather data without API keys
- **AI-Ready:** MCP integration enables Claude to analyze climate data autonomously
- **Cost-Effective:** Open-Meteo is free; versioning is minimal bandwidth
- **Quality Focus:** 5-metric scoring (completeness, outliers, temporal coverage, seasonality, schema)
- **Reproducible:** Quilt versioning enables full audit trails and multi-version analysis
- **Extensible:** Easy to add new locations or data sources

---

## Project Architecture

```
Open-Meteo API / Local Files
    ↓ (Real weather data)
Data Ingestion Layer (downloader.py)
    ↓ (Validate, parse, normalize)
Quality Assessment Engine (quality_checker.py)
    ↓ (5 metrics: completeness, outliers, temporal, seasonality, schema)
Quilt Packaging Layer (quilt_packager.py)
    ↓ (Create versioned packages with metadata)
Quilt Registry (S3 or local)
    ↓
MCPClimateAnalyzer (mcp_analyzer.py)
    ↓ (Claude + MCP for AI-assisted analysis)
Claude / AI Systems
    ↓
Actionable Climate Insights
```

---

## Implementation Plan (3 Phases)

### Phase 1: Foundation ✅ (COMPLETE)
**Goal:** Basic working pipeline with real climate data

**Milestones Achieved:**
- ✅ Successfully fetch Open-Meteo real weather data (NYC 2023-2025)
- ✅ Implemented 5-metric quality scoring (completeness, outliers, temporal, seasonality, schema)
- ✅ Package with Quilt and S3 support (local + cloud)
- ✅ End-to-end pipeline verified (100/100 quality scores)

**Completed Tasks:**
- ✅ Development environment (Poetry, AWS credentials, MCP)
- ✅ ClimateDownloader with CSV validation
- ✅ QualityChecker with 5 climate-specific metrics
- ✅ QuiltPackager with S3 integration
- ✅ PipelineOrchestrator coordinating all stages
- ✅ 68+ comprehensive tests with high coverage

**Deliverables:**
- Working download → assess → package → push pipeline
- One successfully versioned climate package
- Basic quality report JSON
- Demo pipeline with sample data

**Reusable from ClinVar:**
- QuiltPackager (works as-is)
- Pipeline orchestration structure
- Test framework and mocking patterns
- Poetry setup and CI/CD templates

---

### Phase 2: AI Integration & MCP 🚀 (IN PROGRESS)
**Goal:** Enable AI-assisted analysis via Model Context Protocol

**Completed:**
- ✅ MCPClimateAnalyzer with 7 query types:
  - `search` - Find packages by quality/elements
  - `metrics` - Quality metrics extraction
  - `temperature` - Temperature pattern analysis
  - `completeness` - Data completeness by element/station
  - `compare` - Drift detection between versions
  - `sample` - Fetch sample data for AI context
  - `report` - Human-readable summaries

**In Progress:**
- MCP demo showing autonomous Claude analysis
- Documentation for Claude Desktop integration
- API documentation for custom integrations

**Future:**
- [ ] Compare with historical baselines
- [ ] Regional breakdowns (when multi-location data available)
- [ ] Enhanced metadata tagging
- [ ] Quilt MCP server integration (when available)

**Deliverables:**
- Fully functional MCP analyzer
- 7 interactive demos showing Claude capabilities
- MCP integration documentation

---

### Phase 3: Automation & Production Deployment (PLANNED)
**Goal:** Productionize with scheduling, alerts, and multi-location support

**Planned Tasks:**
- [ ] Scheduled execution (AWS Lambda or cron)
- [ ] Quality alerting (email/Slack when thresholds breached)
- [ ] Multi-location data support (add more cities)
- [ ] Historical trend analysis across months/years
- [ ] Integration with Claude API for automated reports
- [ ] Dashboard for quality trends over time

**Deliverables:**
- Fully automated monthly data processing
- AI-generated monthly climate reports
- Multi-location quality monitoring
- Alert system with thresholds
- Complete documentation

---

## Data Source Specifics

### NOAA Climate Data Options

**Option A: Global Historical Climatology Network (GHCN)**
- Daily temperature, precipitation, snow data
- ~20,000 weather stations worldwide
- Free public access
- Monthly releases
- **Good for:** Comprehensive climate monitoring

**Option B: NOAA NCEI Monthly Summaries**
- Pre-aggregated monthly data by region
- Smaller files (~50-100 MB)
- **Good for:** Simpler quality checks, regional analysis

**Option C: Weather.gov API + Historical Data**
- US-focused weather data
- Smaller subset, easier to manage
- **Good for:** Getting started quickly

**Recommendation:** Start with **Option B** (NOAA NCEI Monthly Summaries) for easier QA and smaller files.

---

## Quality Metrics (Climate-Specific)

### Tier 1: Universal Metrics (from ClinVar)
- Data completeness (% non-null values)
- Duplicate records
- Schema stability
- File integrity

### Tier 2: Climate-Specific Metrics
- **Temperature Statistics**
  - Min/max/mean ranges (sanity checks)
  - Outlier detection (>3 std dev from normal)
  - Missing day counts per station

- **Precipitation Data**
  - Zero precipitation percentage (normal)
  - Extreme values (>100mm/day flagged)
  - Consecutive missing days

- **Geographic Coverage**
  - Active station count (stations reporting data)
  - Regional coverage completeness
  - New/inactive stations detected

- **Data Quality Scoring** (similar to ClinVar)
  - Completeness: 30 points
  - Outlier rate: 25 points
  - Geographic coverage: 25 points
  - Schema stability: 10 points
  - Temperature range validity: 10 points

---

## Drift Detection for Climate Data

Compare month-to-month changes:
- Station count changes (>5% flagged)
- Temperature outlier rate increase
- Regional data gaps
- Missing value increases
- Schema modifications
- Severity: Low/Medium/High

**Example:** If July has 15% more missing days than June → drift detected (humidity sensor failures?)

---

## File Structure

```
climate-data-monitor/
├── src/
│   ├── __init__.py
│   ├── downloader.py              # NOAA data ingestion
│   ├── quality_checker.py         # Climate-specific metrics
│   ├── quilt_packager.py          # (reuse from ClinVar, minimal changes)
│   ├── drift_detector.py          # Version comparison
│   └── visualizer.py              # Dashboard & reporting
│
├── scripts/
│   ├── run_pipeline.py            # Main orchestration
│   ├── run_demo_pipeline.py       # Demo with sample data
│   ├── test_s3_integration.py     # S3 validation
│   └── analyze_history.py         # Historical trends
│
├── tests/
│   ├── test_downloader.py
│   ├── test_quality_checker.py
│   ├── test_quilt_packager.py
│   ├── test_pipeline.py
│   └── __init__.py
│
├── config/
│   ├── config.yaml.template
│   ├── demo_config.yaml
│   └── local_test_config.yaml
│
├── data/
│   ├── downloads/                 # NOAA data goes here
│   └── sample_climate_data.csv    # Sample for testing
│
├── output/
│   └── quality_reports/
│
├── docs/
│   ├── README.md
│   ├── architecture.md
│   ├── development.md
│   └── configuration.md
│
├── pyproject.toml                 # Poetry config (reuse from ClinVar)
├── CHANGELOG.md
├── PROJECT_PLAN.md                # This file
└── .gitignore
```

---

## Setup Checklist

- [ ] Create new GitHub repo: `climate-data-monitor`
- [ ] Clone and enter directory
- [ ] Copy `pyproject.toml` from clinvar-data-monitor (mostly reusable)
- [ ] Run `poetry install --with dev`
- [ ] Configure AWS credentials (`aws configure`)
- [ ] Create S3 bucket for climate registry
- [ ] Copy and adapt config templates from ClinVar
- [ ] Create sample climate data CSV
- [ ] Start Phase 1 implementation

---

## Key Differences from ClinVar

| Aspect | ClinVar | Climate |
|--------|---------|---------|
| Data source | NCBI FTP | NOAA API/FTP |
| Data size | 4 GB | 100-200 MB |
| Update freq | Monthly | Monthly |
| Domain metrics | Genetic classification | Temperature/precipitation |
| File format | TSV | CSV/NetCDF |
| Quality focus | Annotation conflicts | Missing data, outliers |
| Ongoing cost | High | Low ✓ |

---

## Reusable Code from ClinVar

### Full Reuse (Copy as-is)
- `src/quilt_packager.py` - Works for any tabular data
- `src/drift_detector.py` - Generic comparison logic (update metrics)
- Pipeline orchestration pattern
- Test framework and fixtures
- Poetry configuration (dependencies)
- GitHub Actions CI/CD template

### Adapt (Modify for climate)
- `src/downloader.py` - Replace ClinVar FTP with NOAA source
- `src/quality_checker.py` - Replace ClinVar metrics with climate metrics
- `config/` - Update for NOAA data paths and climate thresholds
- Documentation - Update for climate domain

### Do Not Reuse (Climate specific)
- None yet - all ClinVar code is adaptable

---

## Testing Strategy

**Target:** 80+ tests (matching ClinVar)

**Distribution:**
- Climate downloader: 16 tests
- Climate quality checker: 24 tests
- Quilt packager: 20 tests (reused from ClinVar)
- Pipeline: 16 tests
- (Optional) Drift detector: 8 tests
- (Optional) Visualizer: 6 tests

**All tests use mocking** - no AWS credentials or network access required for local testing

---

## Success Metrics

### Technical
- [ ] Pipeline executes successfully
- [ ] All 80+ tests passing
- [ ] Demo pipeline completes in <10 seconds
- [ ] Quality report generation works
- [ ] Package versioning works

### Functional
- [ ] Climate metrics are meaningful (detect real data issues)
- [ ] Drift detection flags significant changes
- [ ] Multiple package variants possible
- [ ] Metadata searchable in Quilt

### Operational
- [ ] Code is well-documented
- [ ] Setup takes <30 minutes
- [ ] New developer can run pipeline in 5 minutes
- [ ] S3 costs remain low (<$10/month)

---

## Learning Resources

**From ClinVar Project:**
- [FINAL_STATUS.md](../clinvar-data-monitor/FINAL_STATUS.md) - Design patterns and lessons learned
- [src/quilt_packager.py](../clinvar-data-monitor/src/quilt_packager.py) - Quilt integration example
- [tests/](../clinvar-data-monitor/tests/) - Comprehensive test examples

**Climate Data:**
- [NOAA Climate Data](https://www.ncei.noaa.gov/cdo-web/)
- [GHCN Documentation](https://www.ncei.noaa.gov/products/land-based-station-data-ghcn-daily)

**Quilt & Versioning:**
- [Quilt Documentation](https://docs.quilt.bio/)

---

## Phase 1 Starting Point

### Week 1 Breakdown

**Days 1-2: Setup**
- Create repo structure
- Set up Poetry environment
- Copy/adapt ClinVar base files
- Create sample climate data CSV

**Days 3-4: Downloader**
- Implement ClimateDownloader
- Add NOAA data source fetching
- Write 16 tests

**Days 5-6: Quality Checker**
- Implement climate-specific metrics
- Calculate temperature/precipitation statistics
- Write 24 tests

**Days 7: Integration**
- Test end-to-end pipeline
- Create demo pipeline
- Document setup

---

## Next Steps

1. **Create the repo** - New GitHub repo: `climate-data-monitor`
2. **Initial setup** - Copy structure from ClinVar
3. **Phase 1 start** - Implement downloader and quality checker
4. **Document as you go** - Follow ClinVar's documentation approach
5. **Test first** - TDD: write tests before implementation

---

## Questions to Answer Before Starting

- [ ] Which NOAA dataset to use? (Recommend: NOAA NCEI Monthly Summaries)
- [ ] S3 bucket name? (Suggest: `climate-data-registry` or similar)
- [ ] Geographic focus? (Global, US-only, specific regions?)
- [ ] Metrics priority? (Temperature > Precipitation > Other?)
- [ ] Visualization needs? (Trend charts, missing data heatmap, etc.?)

---

## References & Links

**ClinVar Project (Reference):**
- Status: Archived - See for architecture patterns only
- Key files to review:
  - [FINAL_STATUS.md](../clinvar-data-monitor/FINAL_STATUS.md)
  - [src/quality_checker.py](../clinvar-data-monitor/src/quality_checker.py)
  - [tests/test_quality_checker.py](../clinvar-data-monitor/tests/test_quality_checker.py)

**Tech Stack:**
- Python 3.8+
- Quilt3 (data versioning)
- pandas (data manipulation)
- boto3 (AWS S3)
- pytest (testing)
- Poetry (dependency management)

---

**Created:** November 24, 2025
**Based on:** ClinVar Data Quality Monitor architecture
**Status:** Ready for Phase 1 implementation
