# Climate Data Monitor

Automated data quality monitoring for real climate data with Quilt versioning, S3 integration, and AI-ready MCP support.

## Overview

Climate Data Monitor provides an end-to-end pipeline for:

- **Downloading & Validating** real historical weather data (Open-Meteo API or local files)
- **Assessing Quality** with climate-specific metrics (data completeness, temporal coverage, seasonality confidence, outlier detection)
- **Versioning & Packaging** with Quilt for reproducible, governed data access
- **Publishing to AWS S3** registries for organizational use
- **AI-Ready Analysis** with an MCP-inspired analyzer for autonomous climate insights with Claude

Perfect for scientific teams needing data versioning for regulatory compliance, reproducibility, and cross-functional analysis with AI assistance.

## Quick Start

### Local Testing (Demo Mode)

```bash
# Install dependencies
poetry install

# Run with sample data (no AWS required)
python -m src run --config config/demo_config.yaml
```

### Production with AWS S3

```bash
# Configure AWS credentials
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Run with S3 push enabled
python -m src run --config config/production_config.yaml --push
```

See [PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md) for detailed instructions.

## Architecture

```
Open-Meteo API / Local Files
    ↓
ClimateDownloader (validate, parse, normalize)
    ↓
QualityChecker (5-metric scoring: completeness, outliers, temporal coverage, seasonality, schema)
    ↓
QuiltPackager (versioning, metadata, S3 push)
    ↓
Quilt Registry (S3 or local)
    ↓
MCPClimateAnalyzer (Custom MCP-inspired analyzer for AI analysis)
```

## Project Structure

```
climate-data-monitor/
├── src/
│   ├── __main__.py               # CLI entry point
│   ├── orchestrator.py           # Pipeline coordination
│   ├── downloader.py             # Data ingestion
│   ├── quality_checker.py        # Quality metrics
│   └── quilt_packager.py         # S3 versioning
│
├── tests/
│   ├── test_downloader.py        # 20+ tests
│   ├── test_quality_checker.py   # 20+ tests
│   ├── test_quilt_packager.py    # 21 tests
│   └── test_orchestrator.py      # E2E tests (NEW)
│
├── config/
│   ├── demo_config.yaml          # Local testing
│   ├── production_config.yaml.template  # S3 setup template
│   └── aws_setup.py              # AWS credential validation
│
├── docs/                         # Documentation
│   ├── PIPELINE_GUIDE.md         # Complete usage guide
│   ├── IMPLEMENTATION_SUMMARY.md # Technical details
│   ├── DELIVERY_SUMMARY.md       # Project delivery
│   ├── PROJECT_PLAN.md           # Roadmap
│   └── CHANGELOG.md              # Version history
└── pyproject.toml                # Poetry configuration
```

## CLI Usage

### Run Pipeline

```bash
python -m src run --config <config_file> [options]
```

**Options:**
- `--config` (required) - Path to YAML configuration
- `--data-file` - Override data source with file path
- `--push` - Enable S3 registry push
- `--output` - Save detailed results to JSON

**Examples:**

```bash
# Demo with sample data
python -m src run --config config/demo_config.yaml

# Production with S3 push
python -m src run --config config/production_config.yaml

# Custom data file, save results
python -m src run --config config/demo_config.yaml \
  --data-file path/to/data.csv \
  --output results.json
```

## Features

### Phase 1: Foundation ✅ (Complete)

- ✅ ClimateDownloader - 5-step validation pipeline
- ✅ QualityChecker - 40+ quality metrics
- ✅ QuiltPackager - Quilt integration & S3 support
- ✅ 61+ comprehensive tests (1.5:1 test-to-code ratio)
- ✅ PipelineOrchestrator - End-to-end coordination
- ✅ CLI interface - `python -m src run`
- ✅ AWS credential handling & validation
- ✅ Configuration templates (demo + production)

### Phase 2: Climate-Specific Features (Planned)

- Enhanced drift detection between versions
- Regional quality breakdowns
- Filtered package variants
- Historical trend analysis
- Geographic coverage visualization

### Phase 3: Automation & Monitoring (Planned)

- Scheduled execution (cron/Lambda)
- Quality trend visualization
- Alert system (email/Slack)
- CloudWatch integration
- Deployment documentation

### MCP-Inspired Analysis (Available)

The project includes a custom `MCPClimateAnalyzer` that provides MCP-like functionality for:
- Structured JSON queries (search, metrics, analyze, compare)
- AI-safe data access patterns (no raw SQL needed)
- CLI interface for integration with Claude and other AI systems
- 7 query types for comprehensive climate analysis

**Note:** This is a custom implementation inspired by the Model Context Protocol. For production use of the official Quilt MCP server, see [MCP_INTEGRATION.md](docs/MCP_INTEGRATION.md#official-quilt-mcp-server)

## Quality Scoring

The quality score (0-100) combines 5 actionable metrics:

| Metric | Points | What It Measures |
|--------|--------|------------------|
| Data Completeness | 30 | No missing values (null %) |
| Outlier Rate | 25 | No impossible temperature values |
| Temporal Completeness | 20 | No gaps in date coverage |
| Seasonality Confidence | 15 | Reliable seasonal patterns detected |
| Schema Stability | 10 | All required columns present |

**Score Interpretation:**
- 95-100: Excellent - Production ready
- 85-95: Very Good - Ready for analysis
- 75-85: Good - Usable with caveats
- <75: Fair - Investigate issues

**Real Data Example (NYC 2023-2025):**
- 2024: **100/100** - Perfect: 0% null, no outliers, 365 days covered, 12+ months seasonality
- 2025: **100/100** - Perfect: same as above
- 2023: **99.3/100** - Excellent: 1 temperature outlier detected, otherwise perfect

## Configuration

See [PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md#configuration) for full configuration reference.

**Key sections:**
- `climate` - Data source, download directory
- `quality` - Thresholds for validation
- `quilt` - Package name, S3 bucket, registry
- `aws` - Region, credential validation
- `logging` - Log levels and output

## Testing

Run all tests with coverage:

```bash
pytest tests/ -v --cov=src --cov-report=html
```

Run specific test file:

```bash
pytest tests/test_orchestrator.py -v
```

Current coverage: **61+ tests across 4 modules**

## AWS Setup

### Automated Setup (Recommended)

Use the helper script to automatically create S3 bucket and generate configuration:

```bash
# Interactive mode
poetry run python helper_scripts/setup_aws_s3.py

# Or specify bucket name directly
poetry run python helper_scripts/setup_aws_s3.py --bucket-name my-climate-bucket --region us-west-2
```

This will:
- ✅ Validate AWS credentials
- ✅ Create S3 bucket (with versioning enabled)
- ✅ Block public access
- ✅ Test bucket access
- ✅ Generate `config/production_config.yaml`

### Manual Setup (Alternative)

```bash
# Create and configure bucket
aws s3 mb s3://your-climate-data-bucket --region us-west-2
aws s3api put-bucket-versioning --bucket your-climate-data-bucket --versioning-configuration Status=Enabled

# Configure credentials
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Run pipeline
python -m src run --config config/production_config.yaml
```

## Dependencies

- **quilt3** (≥5.0) - Data versioning & S3 integration
- **pandas** (^2.0.0) - Data manipulation
- **boto3** (^1.26.0) - AWS S3 client
- **pyyaml** (^6.0) - Configuration parsing
- **plotly** (^5.16.0) - Visualization (Phase 2)

Development:
- **pytest** (^7.4.0) - Testing framework
- **black, flake8, isort** - Code quality
- **mypy** (^1.5.0) - Type checking

## Real-World Data

The project includes **3 years of real NYC weather data (2023-2025)** from Open-Meteo API:

- **1,095-1,098 records per year** (365-366 days × 3 elements: TMAX, TMIN, PRCP)
- **0% null data** - Complete daily temperature and precipitation readings
- **Realistic variation** - 51.5% rainy days in 2023 → 46.6% in 2025 (natural climate variation)
- **Quality scores** - 99.3-100/100 (demonstrating excellent data quality)
- **Seasonal patterns** - Clear winter/summer temperature variation for analysis

## Production Use Cases

This project demonstrates:

1. **Real Climate Data Versioning** - Open-Meteo weather data with full reproducibility
2. **Quality Monitoring** - 5-metric scoring for data governance and trend detection
3. **Multi-Version Analysis** - Track quality metrics and seasonal patterns over time
4. **AI-Ready Analysis** - Custom MCP-inspired analyzer for autonomous climate insights with Claude
5. **S3 Integration** - Production-ready AWS deployment with Quilt

## Next Steps

1. **Deploy to production** - Run with your organization's climate data
2. **Enable AI Analysis** - Use the MCP-inspired analyzer or integrate with official Quilt MCP server
3. **Add alerts** - Configure Slack/email for quality thresholds
4. **Schedule runs** - AWS Lambda or cron-based automation

See [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) for the complete roadmap.

## Contributing

- Review code in `src/`
- Check tests in `tests/`
- Update configuration in `config/`
- Reference [docs/PIPELINE_GUIDE.md](docs/PIPELINE_GUIDE.md)

## License

Carriagetown Data Solutions
