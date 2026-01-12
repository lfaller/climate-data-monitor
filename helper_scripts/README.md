# Helper Scripts

Utility scripts to support Climate Data Monitor setup and operations.

## AWS Setup

### `setup_aws_s3.py` - S3 Bucket and Configuration Setup

Automated helper to set up AWS S3 for use as a Quilt registry.

**What it does:**
1. ✅ Validates AWS credentials
2. ✅ Creates S3 bucket (with versioning enabled)
3. ✅ Blocks public access (security best practice)
4. ✅ Tests read/write access
5. ✅ Generates `config/production_config.yaml`

**Interactive mode (recommended for first-time setup):**
```bash
poetry run python helper_scripts/setup_aws_s3.py
```

Prompts for:
- Bucket name (must be globally unique)
- AWS region
- Config file output path

**Command-line mode (automated/scripting):**
```bash
poetry run python helper_scripts/setup_aws_s3.py \
  --bucket-name my-climate-data-bucket \
  --region us-west-2 \
  --config config/production_config.yaml
```

**For existing buckets (skip creation):**
```bash
poetry run python helper_scripts/setup_aws_s3.py \
  --bucket-name existing-bucket \
  --skip-bucket-create
```

**Prerequisites:**
- AWS credentials configured (via environment variables, ~/.aws/credentials, or IAM role)
- `boto3` installed (included in project dependencies)

**Output:**
- Creates S3 bucket with:
  - Versioning enabled (for data governance)
  - Public access blocked (security)
- Generates `config/production_config.yaml` ready to use
- Prints verification steps

**Next steps after setup:**
```bash
# Run pipeline with S3 push enabled
poetry run python -m src run --config config/production_config.yaml

# Verify package in registry
poetry run python -m src analyze --package climate/data
```

---

## Data Sources

### `fetch_open_meteo_data.py` - Download Real Weather Data

Fetch historical weather data from Open-Meteo API and convert to pipeline format.

**Usage:**
```bash
poetry run python helper_scripts/fetch_open_meteo_data.py \
  --lat 40.7128 --lon -74.0060 \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --location "New York City"
```

**Features:**
- Free, no API key required
- Global coverage, 1940-present
- Outputs CSV in pipeline format: `station_id, date, element, value, source_flag`
- Automatically calculates reasonable station IDs from coordinates
- Includes data quality info in output

**Output:**
- CSV file with real weather data (temperature, precipitation)
- Summary statistics (min/max, rainy days %)
- Ready to use with pipeline

**Example - Multiple years for same location:**
```bash
# 2023
poetry run python helper_scripts/fetch_open_meteo_data.py \
  --lat 40.7128 --lon -74.0060 \
  --start-date 2023-01-01 --end-date 2023-12-31 \
  --location "New York City" \
  --output data/real_nyc_2023.csv

# 2024
poetry run python helper_scripts/fetch_open_meteo_data.py \
  --lat 40.7128 --lon -74.0060 \
  --start-date 2024-01-01 --end-date 2024-12-31 \
  --location "New York City" \
  --output data/real_nyc_2024.csv
```

---

### `explore_real_data_sources.py` - Research Data Availability

Documentation and exploration of real climate data sources available for integration.

**Usage:**
```bash
poetry run python helper_scripts/explore_real_data_sources.py
```

**Coverage:**
- NOAA GHCN-Daily (20,000+ stations, 100+ years)
- NOAA ISD-Lite (2,200 stations, 1901-present)
- NOAA CDO Web (search interface)
- Open-Meteo API (free, global, no auth)
- NOAA Weather.gov API (current data, limited historical)

**Output:**
- Comparison of each data source
- Pros/cons and best use cases
- How to access each source
- Recommendation: NOAA GHCN-Daily for production, Open-Meteo for rapid prototyping

---

## Development & Testing

### Running Helper Scripts with Poetry

All helper scripts should be invoked via Poetry to ensure the correct environment:

```bash
poetry run python helper_scripts/<script_name>.py [options]
```

### Adding New Helper Scripts

Place new scripts in this directory with:
1. Clear docstring explaining purpose
2. `main()` function that returns exit code (0 for success)
3. Use `argparse` for CLI arguments
4. Include usage examples in docstring
5. Update this README

---

## Quick Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `setup_aws_s3.py` | Set up AWS S3 bucket & generate config | `poetry run python helper_scripts/setup_aws_s3.py` |
| `fetch_open_meteo_data.py` | Download real weather data | `poetry run python helper_scripts/fetch_open_meteo_data.py --lat X --lon Y --start-date YYYY-MM-DD --end-date YYYY-MM-DD` |
| `explore_real_data_sources.py` | Research available data sources | `poetry run python helper_scripts/explore_real_data_sources.py` |
