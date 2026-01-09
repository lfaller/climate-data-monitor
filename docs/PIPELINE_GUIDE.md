# Climate Data Monitor - Pipeline Execution Guide

This guide covers running the complete end-to-end climate data monitoring pipeline, from data ingestion through quality assessment to Quilt packaging and S3 registry integration.

## Overview

The pipeline coordinates four main phases:

1. **Download & Validate** - Load and validate real climate data (Open-Meteo API or local files)
2. **Quality Assessment** - Calculate 5 quality metrics (completeness, outliers, temporal coverage, seasonality, schema)
3. **Package & Version** - Create Quilt packages with metadata
4. **AI Analysis** (Optional) - Query data via Model Context Protocol (MCP) for Claude analysis

## Quick Start

### Local Testing (Demo Mode)

Run the pipeline with sample data without pushing to AWS:

```bash
python -m src run --config config/demo_config.yaml
```

This will:
- Load real weather data from `data/real_nyc_2024.csv` (or your specified data file)
- Validate the data format and values
- Calculate 5 quality metrics (completeness, outliers, temporal, seasonality, schema)
- Build a Quilt package locally to `~/.quilt/packages`

Expected output:
```
============================================================
Climate Data Monitor - Pipeline Execution Report
============================================================
Status: ✓ SUCCESS
Timestamp: 2026-01-09T13:58:13.000Z
Package: climate/demo-sample

Data File: data/downloads/climate_data_processed_20260109_135813.csv

Quality Metrics:
  Quality Score: 100.0/100
  Rows: 1098
  Null %: 0.00%
  Stations: 1

============================================================
```

### Production with AWS S3

To push packages to an AWS S3 Quilt registry:

#### 1. Set Up AWS Credentials

Choose one method:

**Option A: Environment Variables (Recommended)**
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-west-2
```

**Option B: AWS Credentials File**
```bash
aws configure
# Follow the prompts to enter your access key, secret key, and region
```

**Option C: AWS Profile**
```bash
export AWS_PROFILE=your-profile-name
python -m src run --config config/production_config.yaml
```

#### 2. Create Production Configuration

Copy the template and customize for your AWS setup:

```bash
cp config/production_config.yaml.template config/production_config.yaml
```

Edit `config/production_config.yaml`:

```yaml
quilt:
  bucket: "your-climate-data-bucket"        # Your S3 bucket name
  package_name: "climate/ghcn-daily"        # Package namespace/name
  registry: "s3://your-climate-data-bucket" # Must match bucket
  push_to_registry: true                     # Enable S3 push

aws:
  region: "us-west-2"                        # Your AWS region
  validate_credentials: true                 # Validate before running
  test_bucket_access: true                   # Test bucket access
```

#### 3. Create S3 Bucket

If you don't have an S3 bucket yet:

```bash
aws s3 mb s3://your-climate-data-bucket --region us-west-2
```

#### 4. Run Pipeline

```bash
python -m src run --config config/production_config.yaml
```

Or with the `--push` flag to override config:

```bash
python -m src run --config config/demo_config.yaml --push
```

## CLI Reference

### Basic Usage

```bash
python -m src run --config <config_file> [options]
```

### Options

| Option | Type | Description |
|--------|------|-------------|
| `--config` | Path | **Required.** Path to YAML configuration file |
| `--data-file` | Path | Optional. Override source_url with explicit data file path |
| `--push` | Flag | Enable push to S3 registry (overrides config setting) |
| `--output` | Path | Save detailed JSON results to file |

### Examples

**Run with sample data, save results to JSON:**
```bash
python -m src run --config config/demo_config.yaml --output results.json
```

**Run with custom data file:**
```bash
python -m src run --config config/demo_config.yaml --data-file path/to/my_data.csv
```

**Run with demo config but push to S3:**
```bash
python -m src run --config config/demo_config.yaml --push
```

## Configuration

### Configuration Sections

#### `climate`
Data source and download settings:

```yaml
climate:
  source_url: "file://data/sample_climate_data.csv"  # Data source
  api_key: "demo_mode"                                # API key if needed
  download_dir: "data/downloads"                      # Where to store data
  dataset_id: "GHCN_D"                                # Dataset identifier
  geographic_scope: "production"                      # Informational
```

#### `filtering` (optional)
Filter data by stations or elements:

```yaml
filtering:
  enabled: false
  station_ids: null                    # ["USC00014821", "USC00023182"]
  data_types: null                     # ["TMAX", "TMIN", "PRCP"]
```

#### `quality`
Quality assessment thresholds:

```yaml
quality:
  thresholds:
    min_quality_score: 75              # Minimum acceptable score
    max_null_percentage: 15            # Max null values allowed
    max_outlier_percentage: 5          # Max outliers allowed
    temp_outlier_std_dev: 3            # Temperature outlier threshold
    temp_min_valid: -60                # Minimum valid temperature (°C)
    temp_max_valid: 60                 # Maximum valid temperature (°C)
    precip_max_daily: 500              # Max daily precipitation (mm)
  output_dir: "output/quality_reports" # Where to save reports
```

#### `quilt`
Quilt package settings:

```yaml
quilt:
  bucket: "climate-data-monitor-demo"     # S3 bucket name
  package_name: "climate/demo-sample"     # Package name (namespace/name)
  registry: "s3://climate-data-monitor-demo"  # Registry URL
  push_to_registry: false                 # Push to S3 or build locally
```

#### `aws`
AWS configuration (only needed for S3 push):

```yaml
aws:
  region: "us-west-2"                 # AWS region
  validate_credentials: true          # Validate credentials before run
  test_bucket_access: true            # Test bucket access before run
```

#### `logging`
Logging configuration:

```yaml
logging:
  level: "INFO"                       # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_dir: "logs"                     # Directory for log files
  file_logging: true                  # Enable file logging
  console_logging: true               # Enable console output
```

## Understanding Results

### Output Files

**Processed Data:**
```
data/downloads/climate_data_processed_YYYYMMDD_HHMMSS.csv
```

**Quality Reports:**
```
output/quality_reports/quality_report_YYYYMMDD_HHMMSS.json
```

**Pipeline Logs:**
```
logs/pipeline.log
```

**Detailed Results (if `--output` specified):**
```json
{
  "success": true,
  "data_file": "data/downloads/climate_data_processed_20240112_143200.csv",
  "quality_report": {
    "timestamp": "2024-01-12T14:32:00.000Z",
    "row_count": 200,
    "column_count": 4,
    "quality_score": 87.5,
    "null_percentage_avg": 2.5,
    "duplicate_count": 0,
    "station_count": 5,
    ...
  },
  "package_name": "climate/demo-sample",
  "timestamp": "2024-01-12T14:32:00.000Z",
  "errors": []
}
```

### Quality Score Interpretation

The quality score (0-100) is calculated from:

- **Data Completeness (30%)** - Low null percentage, few duplicates
- **Temperature Metrics (35%)** - Valid ranges, few outliers
- **Precipitation Metrics (15%)** - Reasonable values
- **Geographic Coverage (15%)** - Adequate station count
- **Schema Stability (5%)** - All required columns present

**Score Interpretation:**
- 90-100: Excellent quality
- 75-90: Good quality, acceptable for use
- 50-75: Moderate quality, review results
- Below 50: Poor quality, investigate data source

## Troubleshooting

### AWS Credential Errors

```
ERROR: No AWS credentials found
```

**Solution:**
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
python -m src run --config config/production_config.yaml
```

### Bucket Access Errors

```
ERROR: Access denied to S3 bucket: your-bucket
```

**Solutions:**
- Verify bucket exists: `aws s3 ls s3://your-bucket`
- Check IAM permissions include S3 access
- Verify bucket region matches config

### Data Validation Errors

```
ERROR: Missing required columns: {'element', 'value'}
```

**Solution:**
Ensure your data CSV has these required columns:
- `station_id` - Weather station identifier
- `date` - Observation date (YYYY-MM-DD format)
- `element` - Measurement type (TMAX, TMIN, PRCP, etc.)
- `value` - Numeric measurement value

### Quality Score Too Low

If the quality score is below your configured minimum:

1. Check the quality report JSON for specific issues
2. Review `null_percentage_avg`, `duplicate_count`, outlier counts
3. Adjust thresholds in config if appropriate for your data

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Climate Data Monitor

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  pipeline:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run climate data pipeline
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          python -m src run --config config/production_config.yaml \
            --output results-${{ github.run_id }}.json

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: pipeline-results
          path: results-*.json
```

## Next Steps

- **Phase 2**: Enhanced drift detection and regional breakdowns
- **Phase 3**: Automated scheduling and monitoring with CloudWatch
- **MCP Integration**: Connect with Quilt MCP for AI-assisted analysis

For more information, see [PROJECT_PLAN.md](PROJECT_PLAN.md).
