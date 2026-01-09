# AI Analysis with Climate Data Monitor

## Overview

Climate Data Monitor provides AI-ready analysis capabilities through a custom `MCPClimateAnalyzer` that implements MCP-inspired patterns for climate data queries. This allows Claude and other AI systems to autonomously query, analyze, and generate insights from versioned climate data.

**Key Benefit:** Transform manual data analysis (2-5 days) into AI-assisted workflows (10 minutes).

**Note on Implementation:** This guide describes a custom analyzer that provides MCP-like functionality. For integration with Quilt's official Model Context Protocol server, see the [Official Quilt MCP Server](#official-quilt-mcp-server) section below.

---

## Custom MCP-Inspired Analyzer

The `MCPClimateAnalyzer` in Climate Data Monitor is a custom implementation that provides MCP-like functionality:
- **Search** climate packages by quality and element filters
- **Query** structured data via JSON-safe methods
- **Fetch** sample data and metrics
- **Analyze** temperature trends, completeness, quality metrics
- **Report** human-readable summaries

This custom implementation shares the same design philosophy as the Model Context Protocol: providing structured, AI-safe data access without raw SQL or filesystem operations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 REAL WEATHER DATA SOURCES                       │
│          (Open-Meteo API, Local Files, Other APIs)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           CLIMATE DATA MONITOR PIPELINE                          │
│  Downloader → QualityChecker (5 metrics) → Packager → S3        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          QUILT DATA REGISTRY (Versioned Packages)               │
│        S3 or Local: /Library/Application Support/Quilt          │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
    ┌────────┐         ┌──────────┐        ┌──────────┐
    │ Claude │         │ CLI Tools│        │ Custom AI│
    │Desktop │         │ / Python │        │ Systems  │
    └────────┘         └──────────┘        └──────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼──────────┐
                    │ MCPClimateAnalyzer│
                    │ 7 Query Types:    │
                    │ - search()        │
                    │ - metrics()       │
                    │ - temperature()   │
                    │ - completeness()  │
                    │ - compare()       │
                    │ - sample()        │
                    │ - report()        │
                    └────────┬──────────┘
                             │
                   AI-Driven Insights
```

---

## CLI Commands

The MCP functionality is exposed through CLI commands for testing and integration.

### Basic Syntax

```bash
poetry run python -m src mcp <query_type> [options]
```

### Available Query Types

#### 1. **search** - Find packages matching criteria

```bash
# Search for packages with quality score >= 90
poetry run python -m src mcp search --quality-threshold 90

# Search for packages with specific climate elements
poetry run python -m src mcp search --elements TMAX TMIN PRCP

# Combine filters
poetry run python -m src mcp search --quality-threshold 80 --elements TMAX TMIN
```

**Output:** List of matching packages with metadata

#### 2. **metrics** - Get quality metrics for a package

```bash
poetry run python -m src mcp metrics --package climate/demo-sample
```

**Output:** JSON with:
- Quality score (0-100)
- Data statistics (rows, stations, duplicates)
- Temperature ranges and statistics
- Precipitation statistics
- Data type information

#### 3. **compare** - Compare metrics between packages

```bash
poetry run python -m src mcp compare \
  --package climate/demo-sample \
  --compare-with climate/demo-sample  # In production: compare different versions
```

**Output:** Drift detection showing changes:
- Quality score change
- Row count change
- Station count change
- Temperature trends
- Null percentage changes

#### 4. **sample** - Get sample data from a package

```bash
# Get first 10 rows
poetry run python -m src mcp sample --package climate/demo-sample

# Get first 50 rows
poetry run python -m src mcp sample --package climate/demo-sample --limit 50
```

**Output:** JSON with sample records and column metadata

#### 5. **temperature** - Analyze temperature patterns

```bash
poetry run python -m src mcp temperature --package climate/demo-sample
```

**Output:** JSON with:
- TMAX statistics (min, max, mean, std, quartiles)
- TMIN statistics
- Overall temperature range

#### 6. **completeness** - Analyze data completeness

```bash
poetry run python -m src mcp completeness --package climate/demo-sample
```

**Output:** JSON with:
- Overall null percentage
- Completeness by climate element (TMAX, TMIN, PRCP, etc)
- Completeness by station ID (top 10)

#### 7. **report** - Generate human-readable summary

```bash
poetry run python -m src mcp report --package climate/demo-sample
```

**Output:** Formatted text report with:
- Quality metrics
- Temperature analysis
- Data completeness
- Quality interpretation (EXCELLENT/GOOD/MODERATE/POOR)

---

## Python API Usage

For programmatic access, use the `MCPClimateAnalyzer` class:

```python
from src.mcp_analyzer import MCPClimateAnalyzer

# Initialize analyzer
analyzer = MCPClimateAnalyzer()

# Search packages
results = analyzer.search_packages(quality_threshold=90)

# Get metrics for a package
metrics = analyzer.get_package_metrics("climate/demo-sample")

# Compare packages (drift detection)
comparison = analyzer.compare_packages("climate/month-1", "climate/month-2")

# Get sample data
sample = analyzer.get_data_sample("climate/demo-sample", limit=50)

# Analyze temperature trends
temps = analyzer.analyze_temperature_trends("climate/demo-sample")

# Analyze data completeness
completeness = analyzer.analyze_data_completeness("climate/demo-sample")

# Generate human-readable report
report = analyzer.generate_summary_report("climate/demo-sample")

# Export results to JSON
analyzer.export_analysis_results(metrics, "output/analysis.json")
```

---

## Claude + MCP Integration (Future)

### Option A: Claude Desktop with MCP Plugin

Once Quilt's MCP server is available:

1. **Install Claude Desktop** with MCP support
2. **Configure Quilt MCP** in Claude settings:
   ```json
   {
     "mcp_servers": {
       "quilt": {
         "command": "python",
         "args": ["-m", "quilt.mcp"],
         "env": {
           "QUILT_REGISTRY": "s3://your-bucket"
         }
       }
     }
   }
   ```

3. **Ask Claude questions**:
   ```
   User: "What's the quality trend for January through March?"

   Claude uses MCP to:
   - search_packages() for Jan, Feb, Mar releases
   - get quality_score from each
   - Generate visualization showing trend
   ```

### Option B: Standalone AI Analysis

Use the analyzer programmatically with Claude API:

```python
from src.mcp_analyzer import MCPClimateAnalyzer
import anthropic

analyzer = MCPClimateAnalyzer()

# Gather data
metrics = analyzer.get_package_metrics("climate/demo-sample")
temperature = analyzer.analyze_temperature_trends("climate/demo-sample")

# Send to Claude for analysis
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-opus-20250101",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": f"""Analyze this climate data package:

Quality Metrics: {metrics}
Temperature Analysis: {temperature}

What are the key insights? Are there any concerns?"""
        }
    ]
)

print(response.content[0].text)
```

---

## Use Cases

### 1. Quality Monitoring Dashboards

**User:** "Show me packages with quality scores trending downward"

**MCP Flow:**
1. `search_packages()` - find all packages
2. `compare_packages()` - track quality_score changes
3. Generate alert if threshold breached

### 2. Regional Analysis

**User:** "Which stations have the most missing data?"

**MCP Flow:**
1. `get_data_sample()` - load station data
2. `analyze_data_completeness()` - calculate by station
3. Return ranked list

### 3. Drift Detection

**User:** "Compare last month's data to this month's"

**MCP Flow:**
1. `compare_packages()` - automatic drift detection
2. Highlight changes in:
   - Station count
   - Temperature ranges
   - Null percentages
   - Data quality trends

### 4. Exploratory Analysis

**User:** "Show me temperature trends over the past 6 months"

**MCP Flow:**
1. `search_packages()` - find all monthly releases
2. `analyze_temperature_trends()` - for each month
3. Combine results into trend visualization

---

## Benefits of MCP Integration

| Traditional Analysis | With MCP |
|---------------------|----------|
| Manual package discovery | Automated search with filters |
| Write SQL queries | Natural language requests |
| Download data locally | Query in-place (S3) |
| Manual visualization | AI generates charts |
| Reproducibility unclear | Full provenance/audit trail |
| Days to analyze | Minutes with Claude |

---

## Demo Workflow

### Step 1: Create Packages

```bash
# Run the pipeline to create versioned packages
poetry run python -m src run --config config/demo_config.yaml
```

### Step 2: Query with MCP

```bash
# Get metrics
poetry run python -m src mcp metrics

# Get report
poetry run python -m src mcp report

# Analyze temperature
poetry run python -m src mcp temperature

# Check completeness
poetry run python -m src mcp completeness
```

### Step 3: AI Analysis (Using Claude API)

```python
from src.mcp_analyzer import MCPClimateAnalyzer
import anthropic

analyzer = MCPClimateAnalyzer()
metrics = analyzer.get_package_metrics("climate/demo-sample")
report = analyzer.generate_summary_report("climate/demo-sample")

# Send to Claude
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-opus-20250101",
    max_tokens=500,
    messages=[
        {
            "role": "user",
            "content": f"Analyze this climate data quality report:\n\n{report}"
        }
    ]
)

print("Claude's Analysis:")
print(response.content[0].text)
```

---

## Official Quilt MCP Server

**Current Status:** Climate Data Monitor uses a custom analyzer. Quilt has released an official Model Context Protocol server.

### Why Two Options?

**Custom MCPClimateAnalyzer (Current):**
- ✅ Works immediately without additional setup
- ✅ Optimized for climate data patterns
- ✅ 7 query types specific to weather analysis
- ❌ Not protocol-compliant (no stdio/HTTP)
- ❌ CLI-only integration
- **Use for:** Quick CLI testing, Claude API integration without MCP protocol

**Official Quilt MCP Server:**
- ✅ Protocol-compliant (stdio-based communication)
- ✅ Works with Claude Desktop and other MCP clients
- ✅ Maintained by Quilt team
- ✅ Supports all Quilt packages (not just climate)
- ❌ Requires additional setup
- **Use for:** Production deployments, Claude Desktop integration, cross-domain analysis

### Migrating to Official Quilt MCP Server

If you want to use Quilt's official MCP server:

1. **Install quilt-mcp-server:**
   ```bash
   pip install quilt-mcp-server
   # Or build from source:
   # https://github.com/quiltdata/quilt-mcp-server
   ```

2. **Configure Claude Desktop** (if using MCP):
   ```json
   {
     "mcp_servers": {
       "quilt": {
         "command": "quilt-mcp-server",
         "env": {
           "QUILT_REGISTRY": "s3://your-bucket"
         }
       }
     }
   }
   ```

3. **Use with Claude Desktop:**
   - Claude will have access to Quilt's official MCP tools
   - Query climate packages along with other Quilt data
   - Full protocol compliance for robustness

### Reference

- **Quilt MCP Server Repository:** https://github.com/quiltdata/quilt-mcp-server
- **Model Context Protocol Spec:** https://modelcontextprotocol.io
- **Quilt Documentation:** https://quiltdata.com/docs

---

## File Organization

```
src/
├── __main__.py              # CLI entry point (includes 'mcp' command)
├── mcp_analyzer.py          # MCPClimateAnalyzer class
├── quilt_analyzer.py        # Quilt package interface
├── orchestrator.py          # Pipeline orchestration
├── downloader.py            # Data ingestion
├── quality_checker.py       # Quality metrics
└── quilt_packager.py        # Quilt packaging

docs/
├── MCP_INTEGRATION.md       # This file
├── PIPELINE_GUIDE.md        # Usage guide
├── IMPLEMENTATION_SUMMARY.md # Technical details
└── PROJECT_PLAN.md          # Roadmap
```

---

## Next Steps

### For Local Testing (Custom Analyzer)
1. Run `poetry run python -m src mcp report` to verify setup
2. Explore different query types
3. Test with your own climate packages
4. Use with Claude API for AI analysis (see CHANGELOG.md for example)

### For Production (Choose Your Path)

**Option A: Continue with Custom Analyzer**
1. Deploy MCPClimateAnalyzer to AWS Lambda
2. Integrate with Claude API for autonomous analysis
3. Set up CloudWatch alarms for quality thresholds
4. Create automated email/Slack alerts

**Option B: Migrate to Official Quilt MCP Server**
1. Install quilt-mcp-server (see [Official Quilt MCP Server](#official-quilt-mcp-server) section)
2. Set up Claude Desktop with MCP plugin
3. Deploy as stdio-based service
4. Leverage full MCP protocol compliance

---

## Troubleshooting

### "Package not found"
- Verify package name: `quilt3.Package.browse("climate/demo-sample")`
- Check Quilt registry path: `/Users/username/Library/Application Support/Quilt/packages`

### "No data returned"
- Ensure pipeline has run: `poetry run python -m src run --config config/demo_config.yaml`
- Check that packages are in correct registry location

### JSON parsing errors
- Redirect to file: `poetry run python -m src mcp metrics > output.json`
- Verify valid JSON with: `python -m json.tool output.json`

---

## Related Documentation

- [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) - How to run the pipeline
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Architecture details
- [PROJECT_PLAN.md](PROJECT_PLAN.md) - Roadmap and future work
- [Quilt Documentation](https://quiltdata.com/docs) - Official Quilt docs
- [Claude API Documentation](https://claude.ai/api/docs) - Claude integration guide

---

**Last Updated:** January 8, 2026
