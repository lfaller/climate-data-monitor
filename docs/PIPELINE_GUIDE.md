# Pipeline Execution Guide

## Quick Start

### Local Testing (Demo)

```bash
poetry install
poetry run python -m src run --config config/demo_config.yaml
```

Expected output:
```
============================================================
Climate Data Monitor - Pipeline Execution Report
============================================================
Status: ✓ SUCCESS
Package: climate/demo
Quality Score: 99/100
Rows: 20
============================================================
```

### Production with S3

```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Create S3 bucket
aws s3 mb s3://your-bucket-name --region us-west-2
aws s3api put-bucket-versioning \
  --bucket your-bucket-name \
  --versioning-configuration Status=Enabled

# Update config
sed -i '' 's|climate-data-monitor-quilt|your-bucket-name|' config/production_config.yaml

# Run with S3 push
poetry run python -m src run --config config/production_config.yaml --push
```

## Configuration

Configs are simple YAML files with 3 sections:

### `climate` section
```yaml
climate:
  source_url: file://data/real_nyc_2024.csv  # Data file path
  download_dir: data/downloads               # Temp storage
```

### `quality` section
```yaml
quality:
  thresholds:
    min_quality_score: 75              # Minimum acceptable score
    max_null_percentage: 15            # Max null values allowed
    temp_outlier_std_dev: 3            # Outlier detection sensitivity
    precip_max_daily: 500              # Max daily precipitation (mm)
  output_dir: output/quality_reports   # Report output location
```

### `quilt` section
```yaml
quilt:
  package_name: climate/nyc-2024       # Quilt package name
  registry: s3://your-bucket           # Registry URL (s3:// or local)
```

## CLI Options

```bash
# Basic run
python -m src run --config config/demo_config.yaml

# Override data file
python -m src run --config config/demo_config.yaml \
  --data-file path/to/data.csv

# Enable S3 push
python -m src run --config config/production_config.yaml --push

# Save results to JSON
python -m src run --config config/demo_config.yaml \
  --output results.json
```

## Pipeline Stages

### Stage 1: Download & Validate
- Loads CSV file
- Validates required columns (station_id, date, element, value)
- Validates date format (YYYY-MM-DD)
- Validates numeric values
- Removes invalid rows

### Stage 2: Quality Assessment
Calculates 5 metrics:
- **Data Completeness** (30 pts) - Null percentage
- **Outlier Rate** (25 pts) - Temperature anomalies
- **Temporal Completeness** (20 pts) - Date coverage
- **Seasonality Confidence** (15 pts) - Pattern reliability
- **Schema Stability** (10 pts) - Required columns present

### Stage 3: Package & Version
- Creates Quilt package
- Attaches quality report metadata
- Pushes to registry (local or S3)

## Quality Score Interpretation

- **95-100**: Excellent data quality
- **85-95**: Very good, ready for analysis
- **75-85**: Good, usable with review
- **<75**: Investigate data issues

## Troubleshooting

**AWS credentials error:**
```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
# or use: aws configure
```

**S3 bucket not found:**
- Check bucket exists: `aws s3 ls`
- Check versioning: `aws s3api get-bucket-versioning --bucket your-bucket`

**Data validation errors:**
- Check CSV columns: station_id, date, element, value
- Check date format: YYYY-MM-DD
- Check numeric values for temperature/precipitation

## Testing

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=html

# Specific test
pytest tests/test_quality_checker.py -v
```
