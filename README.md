# Climate Data Monitor

A production-quality data pipeline that validates climate data, calculates quality metrics, and publishes versioned packages to Quilt registries.

## What It Does

Climate Data Monitor demonstrates a complete data engineering workflow:

1. **Validates** climate CSV data with multi-stage validation pipeline
2. **Assesses Quality** with 5 actionable metrics (completeness, outliers, temporal coverage, seasonality, schema)
3. **Versions** data using Quilt for reproducible, governed access
4. **Publishes** to S3 registries or local Quilt packages

## Quick Start

### Demo (local, no AWS required)

```bash
poetry install
poetry run python -m src run --config config/demo_config.yaml
```

### Production (with Quilt + S3)

```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

poetry run python -m src run --config config/production_config.yaml --push
```

## Pipeline Architecture

```
CSV Data
  ↓
ClimateDownloader (multi-stage validation)
  ↓
QualityChecker (5-metric scoring)
  ↓
QuiltPackager (versioning & packaging)
  ↓
Quilt Registry (local or S3)
```

## Project Structure

```
climate-data-monitor/
├── src/
│   ├── __main__.py           # CLI entry point
│   ├── orchestrator.py       # Pipeline coordination (291 lines)
│   ├── downloader.py         # Data validation (325 lines)
│   ├── quality_checker.py    # Quality metrics (501 lines)
│   └── quilt_packager.py     # Versioning (337 lines)
├── tests/                    # 68 focused tests, 1:1 ratio with code
├── config/
│   ├── demo_config.yaml      # Local testing
│   └── production_config.yaml # S3 publishing
├── data/
│   ├── sample_climate_data.csv      # For testing
│   ├── real_nyc_2024.csv            # Real weather data
│   └── real_nyc_2025.csv            # Real weather data
└── docs/
    ├── README.md             # This file
    └── PIPELINE_GUIDE.md     # Usage & configuration
```

## Quality Scoring

Quality score (0-100) combines 5 actionable metrics:

| Metric | Points | Measures |
|--------|--------|----------|
| Data Completeness | 30 | Null value percentage |
| Outlier Rate | 25 | Invalid temperature values |
| Temporal Completeness | 20 | Date coverage |
| Seasonality Confidence | 15 | Seasonal pattern reliability |
| Schema Stability | 10 | Required columns present |

**Real data results:**
- 2024: 100/100 (perfect)
- 2025: 100/100 (perfect)

## Configuration

### Demo Config
```yaml
climate:
  source_url: file://data/sample_climate_data.csv
  download_dir: data/downloads

quality:
  thresholds:
    min_quality_score: 75
    max_null_percentage: 15
    temp_outlier_std_dev: 3
    precip_max_daily: 500
  output_dir: output/quality_reports

quilt:
  package_name: climate/demo
  registry: local
```

### Production Config
```yaml
climate:
  source_url: file://data/real_nyc_2024.csv
  download_dir: data/downloads

quality:
  thresholds:
    min_quality_score: 75
    max_null_percentage: 15
    temp_outlier_std_dev: 3
    precip_max_daily: 500
  output_dir: output/quality_reports

quilt:
  package_name: climate/nyc-2024
  registry: s3://climate-data-monitor-quilt
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html
```

**Coverage: 68 tests across 4 modules (1:1 test-to-code ratio)**

## Dependencies

- **quilt3** (≥5.0) - Data versioning & S3
- **pandas** (^2.0.0) - Data processing
- **boto3** (^1.26.0) - AWS S3 client
- **pyyaml** (^6.0) - Config parsing

Dev:
- **pytest** (^7.4.0) - Testing
- **black, flake8, isort** - Code quality
- **mypy** (^1.5.0) - Type checking

## AWS Setup

Configure AWS credentials:
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

Create S3 bucket and enable versioning:
```bash
aws s3 mb s3://your-bucket-name --region us-west-2
aws s3api put-bucket-versioning \
  --bucket your-bucket-name \
  --versioning-configuration Status=Enabled
```

Update `config/production_config.yaml` with your bucket name, then run with `--push` flag.

## Real Data

Includes 2 years of real NYC weather data from Open-Meteo API:
- 2024: 366 days × 3 elements = 1,098 records (100/100 quality)
- 2025: 365 days × 3 elements = 1,095 records (100/100 quality)

Elements tracked: Temperature (TMAX, TMIN, TOBS), Precipitation (PRCP)

## CLI Usage

```bash
# Run pipeline with config
python -m src run --config config/demo_config.yaml

# Override data source
python -m src run --config config/demo_config.yaml --data-file path/to/data.csv

# Enable S3 push
python -m src run --config config/production_config.yaml --push

# Save results to JSON
python -m src run --config config/demo_config.yaml --output results.json
```

## Key Features & Skills Demonstrated

This project showcases:

1. **Data Engineering** - Multi-stage validation pipeline with domain-specific logic
2. **Software Engineering** - Clean architecture, comprehensive testing, proper error handling
3. **AWS Integration** - S3, boto3, credential management
4. **Data Versioning** - Quilt3 integration for reproducible data access
5. **Production Quality** - Real data, realistic metrics, deployment-ready code

~1,500 lines of focused, well-tested Python code with zero technical debt.

## License

Carriagetown Data Solutions
