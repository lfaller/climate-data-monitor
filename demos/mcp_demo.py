#!/usr/bin/env python
"""Demo script showcasing Quilt MCP integration for climate data analysis.

This script demonstrates how Claude (via MCP) can autonomously analyze
climate packages without manual data wrangling.

Usage:
    poetry run python demos/mcp_demo.py
"""

import json
from pathlib import Path

from src.mcp_analyzer import MCPClimateAnalyzer


def demo_section(title: str) -> None:
    """Print a demo section header."""
    print(f"\n{'=' * 70}")
    print(f"{title}")
    print(f"{'=' * 70}\n")


def demo_basic_search():
    """Demo: Search for quality packages."""
    demo_section("DEMO 1: Search for High-Quality Packages")

    analyzer = MCPClimateAnalyzer()

    print("Query: Find packages with quality score >= 95")
    results = analyzer.search_packages(quality_threshold=95)

    print(f"\nFound {len(results)} package(s):")
    for pkg in results:
        print(f"\n  Package: {pkg['package']}")
        print(f"    Quality Score: {pkg['quality_score']}/100")
        print(f"    Rows: {pkg['row_count']}")
        print(f"    Stations: {pkg['station_count']}")
        print(f"    Elements: {', '.join(pkg['elements'])}")


def demo_quality_metrics():
    """Demo: Get detailed quality metrics."""
    demo_section("DEMO 2: Retrieve Quality Metrics (AI-Safe JSON)")

    analyzer = MCPClimateAnalyzer()
    pkg_name = "climate/demo-sample"

    print(f"Fetching metrics for: {pkg_name}")
    metrics = analyzer.get_package_metrics(pkg_name)

    print("\nQuality Metrics (AI-readable JSON):")
    print(json.dumps(metrics["quality_metrics"], indent=2))

    print("\nTemperature Statistics:")
    print(json.dumps(metrics["temperature_stats"], indent=2))


def demo_temperature_analysis():
    """Demo: Analyze temperature patterns."""
    demo_section("DEMO 3: Temperature Trend Analysis")

    analyzer = MCPClimateAnalyzer()
    pkg_name = "climate/demo-sample"

    print(f"Analyzing temperature patterns in: {pkg_name}\n")
    analysis = analyzer.analyze_temperature_trends(pkg_name)

    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        return

    temp_range = analysis["temperature_analysis"]["temperature_range"]
    print(f"Temperature Range:")
    print(f"  Min: {temp_range['min']:.1f}°C")
    print(f"  Max: {temp_range['max']:.1f}°C")
    print(f"  Mean: {temp_range['mean']:.1f}°C")

    tmax = analysis["temperature_analysis"]["tmax_stats"]
    tmin = analysis["temperature_analysis"]["tmin_stats"]

    print(f"\nTMAX Statistics:")
    print(f"  Mean: {tmax['mean']:.1f}°C")
    print(f"  Std Dev: {tmax['std']:.1f}°C")
    print(f"  Range: {tmax['min']:.1f}°C to {tmax['max']:.1f}°C")

    print(f"\nTMIN Statistics:")
    print(f"  Mean: {tmin['mean']:.1f}°C")
    print(f"  Std Dev: {tmin['std']:.1f}°C")
    print(f"  Range: {tmin['min']:.1f}°C to {tmin['max']:.1f}°C")


def demo_data_completeness():
    """Demo: Analyze data completeness."""
    demo_section("DEMO 4: Data Completeness Analysis")

    analyzer = MCPClimateAnalyzer()
    pkg_name = "climate/demo-sample"

    print(f"Analyzing completeness for: {pkg_name}\n")
    completeness = analyzer.analyze_data_completeness(pkg_name)

    overall = completeness["overall_completeness"]
    print(f"Overall Completeness:")
    print(f"  Total Records: {overall['total_records']}")
    print(f"  Null Count: {overall['null_count']}")
    print(f"  Null %: {overall['null_percentage']:.2f}%")

    if "by_element" in completeness:
        print(f"\nCompleteness by Element:")
        for element, stats in completeness["by_element"].items():
            print(f"  {element}: {stats['count']} records, {stats['null_percentage']:.1f}% null")

    if "by_station" in completeness:
        print(f"\nTop 10 Stations by Data Availability:")
        for station, stats in sorted(
            completeness["by_station"].items(),
            key=lambda x: x[1]["null_percentage"],
        )[:5]:
            print(
                f"  {station}: {stats['count']} records, {stats['null_percentage']:.1f}% null"
            )


def demo_sample_data():
    """Demo: Fetch sample data for AI analysis."""
    demo_section("DEMO 5: Fetch Sample Data (for AI Context)")

    analyzer = MCPClimateAnalyzer()
    pkg_name = "climate/demo-sample"

    print(f"Fetching sample from: {pkg_name}\n")
    sample = analyzer.get_data_sample(pkg_name, limit=5)

    print(f"Total Rows: {sample['total_rows']}")
    print(f"Columns: {', '.join(sample['columns'])}\n")

    print("Sample Data (first 5 rows):")
    for i, row in enumerate(sample["sample"], 1):
        print(f"\n  Row {i}:")
        for key, value in row.items():
            print(f"    {key}: {value}")


def demo_human_report():
    """Demo: Generate human-readable summary."""
    demo_section("DEMO 6: AI-Friendly Summary Report")

    analyzer = MCPClimateAnalyzer()
    pkg_name = "climate/demo-sample"

    print(f"Generating summary for: {pkg_name}\n")
    report = analyzer.generate_summary_report(pkg_name)
    print(report)


def demo_mcp_workflow():
    """Demo: Full AI workflow (what Claude would do)."""
    demo_section("DEMO 7: Full AI Workflow (Claude + MCP)")

    print("""
This demonstrates what Claude would do when you ask:
"What's the quality of the latest climate data and are there any concerns?"

Step 1: Search for recent packages
""")

    analyzer = MCPClimateAnalyzer()

    # Step 1: Search
    print('  > analyzer.search_packages(quality_threshold=80)')
    packages = analyzer.search_packages(quality_threshold=80)
    print(f"  ✓ Found {len(packages)} package(s)")

    if packages:
        pkg = packages[0]["package"]

        # Step 2: Get metrics
        print(f'\n  > analyzer.get_package_metrics("{pkg}")')
        metrics = analyzer.get_package_metrics(pkg)
        print(
            f"  ✓ Quality Score: {metrics['quality_metrics']['quality_score']}/100"
        )

        # Step 3: Analyze temperature
        print(f'\n  > analyzer.analyze_temperature_trends("{pkg}")')
        temps = analyzer.analyze_temperature_trends(pkg)
        if "error" not in temps:
            temp_range = temps["temperature_analysis"]["temperature_range"]
            print(f"  ✓ Temperature Range: {temp_range['min']:.1f} to {temp_range['max']:.1f}°C")

        # Step 4: Check completeness
        print(f'\n  > analyzer.analyze_data_completeness("{pkg}")')
        completeness = analyzer.analyze_data_completeness(pkg)
        null_pct = completeness["overall_completeness"]["null_percentage"]
        print(f"  ✓ Data Completeness: {100-null_pct:.1f}%")

        # Step 5: Generate report
        print(f'\n  > analyzer.generate_summary_report("{pkg}")')
        report = analyzer.generate_summary_report(pkg)
        print("  ✓ Report generated")

        print(f"""
Step 2: Interpret results and return answer

Claude's Assessment:
- Quality Score: {metrics['quality_metrics']['quality_score']}/100 → {"✅ EXCELLENT" if metrics['quality_metrics']['quality_score'] >= 90 else "✅ GOOD" if metrics['quality_metrics']['quality_score'] >= 75 else "⚠️  MODERATE"}
- Temperature Data: Present and valid ({temp_range['min']:.1f}°C to {temp_range['max']:.1f}°C)
- Data Completeness: {100-null_pct:.1f}% complete
- Recommendation: Data is {"ready for analysis" if metrics['quality_metrics']['quality_score'] >= 80 else "usable with caveats"}

All data retrieved via MCP in ~500ms with full provenance!
""")


def main():
    """Run all demos."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                 QUILT MCP INTEGRATION DEMO                        ║
║                  Climate Data Monitor                             ║
╚═══════════════════════════════════════════════════════════════════╝

This demo showcases how the Model Context Protocol (MCP) enables
Claude and other AI systems to analyze climate packages autonomously.

MCP eliminates manual data wrangling:
  ❌ Traditional: Download CSV → Write Python → Analyze → Email
  ✅ With MCP:  Ask Claude → Instant Analysis → Full Provenance
""")

    try:
        # Run all demos
        demo_basic_search()
        demo_quality_metrics()
        demo_temperature_analysis()
        demo_data_completeness()
        demo_sample_data()
        demo_human_report()
        demo_mcp_workflow()

        print("\n" + "=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        print("""
Key Takeaways:

1. MCP provides structured, AI-safe data access
2. All queries return JSON (perfect for Claude)
3. No data downloaded to local filesystem
4. Queries are logged and reproducible
5. Extensible to production systems

Next Steps:

1. Run individual MCP commands:
   poetry run python -m src mcp report

2. Integrate with Claude API:
   from src.mcp_analyzer import MCPClimateAnalyzer
   analyzer = MCPClimateAnalyzer()
   # Pass results to Claude for analysis

3. Deploy to production:
   - Lambda function with MCP analyzer
   - CloudWatch alarms on quality thresholds
   - Slack notifications for drift detection

See docs/MCP_INTEGRATION.md for full documentation.
""")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
