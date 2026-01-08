"""MCP-compatible analyzer for Quilt climate packages.

This module provides tools for Claude and other AI systems to query,
analyze, and generate insights from climate data packages via the
Quilt MCP server.

Compatible with: Quilt Model Context Protocol (MCP)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd

from .quilt_analyzer import QuiltPackageAnalyzer

logger = logging.getLogger(__name__)


class MCPClimateAnalyzer:
    """AI-friendly analyzer for climate packages via MCP."""

    def __init__(self, registry_url: Optional[str] = None):
        """Initialize the MCP analyzer.

        Args:
            registry_url: S3 URL or local path to Quilt registry
        """
        self.registry_url = registry_url or "file://local"
        self.cache = {}

    def search_packages(
        self,
        quality_threshold: Optional[float] = None,
        element_filter: Optional[List[str]] = None,
        station_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for climate packages matching criteria.

        This simulates the Quilt MCP search.unified_search() capability.

        Args:
            quality_threshold: Only return packages with quality >= this value
            element_filter: Filter by climate elements (TMAX, TMIN, PRCP, etc)
            station_filter: Filter by station IDs

        Returns:
            List of package summaries matching criteria
        """
        results = []

        # In a real MCP scenario, this would query the S3 registry
        # For now, we'll search local packages
        try:
            # Default: search climate/demo-sample
            analyzer = QuiltPackageAnalyzer("climate/demo-sample")
            metrics = analyzer.get_quality_metrics()

            # Check quality threshold
            if quality_threshold and metrics["quality_score"] < quality_threshold:
                return results

            package_info = {
                "package": "climate/demo-sample",
                "quality_score": metrics["quality_score"],
                "row_count": metrics["row_count"],
                "station_count": metrics["station_count"],
                "timestamp": metrics["timestamp"],
                "elements": analyzer.get_data_summary().get("unique_elements", []),
            }

            # Apply filters
            if element_filter:
                elements = set(package_info["elements"])
                if not elements.intersection(set(element_filter)):
                    return results

            results.append(package_info)
        except Exception as e:
            logger.warning(f"Error searching packages: {e}")

        return results

    def get_package_metrics(self, package_name: str) -> Dict[str, Any]:
        """Get quality metrics for a specific package.

        This simulates tabulator.table_query() for metadata.

        Args:
            package_name: Package name (e.g., "climate/demo-sample")

        Returns:
            Dictionary of quality metrics and statistics
        """
        try:
            analyzer = QuiltPackageAnalyzer(package_name)

            return {
                "package": package_name,
                "quality_metrics": analyzer.get_quality_metrics(),
                "temperature_stats": analyzer.get_temperature_stats(),
                "precipitation_stats": analyzer.get_precipitation_stats(),
                "data_summary": analyzer.get_data_summary(),
            }
        except Exception as e:
            logger.error(f"Error getting metrics for {package_name}: {e}")
            return {"error": str(e)}

    def compare_packages(
        self, package_a: str, package_b: str
    ) -> Dict[str, Any]:
        """Compare quality metrics between two packages.

        Shows trends and changes (drift detection).

        Args:
            package_a: First package name
            package_b: Second package name

        Returns:
            Comparison report with changes and trends
        """
        try:
            metrics_a = self.get_package_metrics(package_a)
            metrics_b = self.get_package_metrics(package_b)

            if "error" in metrics_a or "error" in metrics_b:
                return {"error": "Failed to load one or both packages"}

            qa = metrics_a["quality_metrics"]
            qb = metrics_b["quality_metrics"]

            return {
                "comparison": {
                    "package_a": package_a,
                    "package_b": package_b,
                    "quality_score_change": qb["quality_score"] - qa["quality_score"],
                    "row_count_change": qb["row_count"] - qa["row_count"],
                    "station_count_change": qb["station_count"] - qa["station_count"],
                    "null_percentage_change": (
                        qb["null_percentage_avg"] - qa["null_percentage_avg"]
                    ),
                },
                "temperature_trends": {
                    "tmax_change": (
                        metrics_b["temperature_stats"].get("tmax_mean", 0)
                        - metrics_a["temperature_stats"].get("tmax_mean", 0)
                    ),
                    "tmin_change": (
                        metrics_b["temperature_stats"].get("tmin_mean", 0)
                        - metrics_a["temperature_stats"].get("tmin_mean", 0)
                    ),
                },
            }
        except Exception as e:
            logger.error(f"Error comparing packages: {e}")
            return {"error": str(e)}

    def get_data_sample(
        self, package_name: str, limit: int = 10
    ) -> Dict[str, Any]:
        """Fetch sample data from a package.

        This simulates buckets.object_fetch().

        Args:
            package_name: Package name
            limit: Number of rows to return

        Returns:
            Sample data and metadata
        """
        try:
            analyzer = QuiltPackageAnalyzer(package_name)
            data = analyzer.load_data()

            return {
                "package": package_name,
                "total_rows": len(data),
                "columns": list(data.columns),
                "sample": data.head(limit).to_dict("records"),
                "dtypes": data.dtypes.to_dict(),
            }
        except Exception as e:
            logger.error(f"Error fetching sample: {e}")
            return {"error": str(e)}

    def analyze_temperature_trends(
        self, package_name: str
    ) -> Dict[str, Any]:
        """Analyze temperature patterns in a package.

        Args:
            package_name: Package name

        Returns:
            Temperature analysis report
        """
        try:
            analyzer = QuiltPackageAnalyzer(package_name)
            data = analyzer.load_data()

            if "element" not in data.columns or "value" not in data.columns:
                return {"error": "Package missing required columns"}

            temp_data = data[data["element"].isin(["TMAX", "TMIN"])]

            if temp_data.empty:
                return {"error": "No temperature data found"}

            analysis = {
                "package": package_name,
                "temperature_analysis": {
                    "tmax_stats": (
                        temp_data[temp_data["element"] == "TMAX"]["value"]
                        .describe()
                        .to_dict()
                    ),
                    "tmin_stats": (
                        temp_data[temp_data["element"] == "TMIN"]["value"]
                        .describe()
                        .to_dict()
                    ),
                    "temperature_range": {
                        "min": float(temp_data["value"].min()),
                        "max": float(temp_data["value"].max()),
                        "mean": float(temp_data["value"].mean()),
                    },
                },
            }

            return analysis
        except Exception as e:
            logger.error(f"Error analyzing temperature: {e}")
            return {"error": str(e)}

    def analyze_data_completeness(
        self, package_name: str
    ) -> Dict[str, Any]:
        """Analyze data completeness by element and station.

        Args:
            package_name: Package name

        Returns:
            Completeness analysis
        """
        try:
            analyzer = QuiltPackageAnalyzer(package_name)
            data = analyzer.load_data()

            completeness = {
                "package": package_name,
                "overall_completeness": {
                    "total_records": len(data),
                    "null_count": int(data.isnull().sum().sum()),
                    "null_percentage": float(
                        (data.isnull().sum().sum() / (len(data) * len(data.columns)))
                        * 100
                    ),
                },
            }

            # By element
            if "element" in data.columns:
                by_element = {}
                for element in data["element"].unique():
                    element_data = data[data["element"] == element]
                    by_element[element] = {
                        "count": len(element_data),
                        "null_percentage": float(
                            (element_data.isnull().sum().sum() / len(element_data))
                            * 100
                        ),
                    }
                completeness["by_element"] = by_element

            # By station
            if "station_id" in data.columns:
                by_station = {}
                for station in data["station_id"].unique()[:10]:  # Top 10
                    station_data = data[data["station_id"] == station]
                    by_station[station] = {
                        "count": len(station_data),
                        "null_percentage": float(
                            (station_data.isnull().sum().sum() / len(station_data))
                            * 100
                        ),
                    }
                completeness["by_station"] = by_station

            return completeness
        except Exception as e:
            logger.error(f"Error analyzing completeness: {e}")
            return {"error": str(e)}

    def generate_summary_report(self, package_name: str) -> str:
        """Generate a human-readable summary report.

        Args:
            package_name: Package name

        Returns:
            Formatted text report
        """
        try:
            metrics = self.get_package_metrics(package_name)
            temp_trends = self.analyze_temperature_trends(package_name)
            completeness = self.analyze_data_completeness(package_name)

            report = f"""
CLIMATE DATA PACKAGE ANALYSIS REPORT
{'=' * 70}

Package: {package_name}
Generated: {datetime.now().isoformat()}

QUALITY METRICS
{'-' * 70}
Quality Score: {metrics['quality_metrics']['quality_score']:.1f}/100
Rows: {metrics['quality_metrics']['row_count']}
Stations: {metrics['quality_metrics']['station_count']}
Null Percentage: {metrics['quality_metrics']['null_percentage_avg']:.2f}%
Duplicates: {metrics['quality_metrics']['duplicate_count']}

TEMPERATURE ANALYSIS
{'-' * 70}
"""
            if "error" not in temp_trends:
                temp_stats = temp_trends.get("temperature_analysis", {}).get(
                    "temperature_range", {}
                )
                report += f"""
Min Temperature: {temp_stats.get('min', 'N/A'):.1f}°C
Max Temperature: {temp_stats.get('max', 'N/A'):.1f}°C
Mean Temperature: {temp_stats.get('mean', 'N/A'):.1f}°C
"""

            report += f"""
DATA COMPLETENESS
{'-' * 70}
Overall Null %: {completeness.get('overall_completeness', {}).get('null_percentage', 0):.2f}%

INTERPRETATION
{'-' * 70}
"""
            quality_score = metrics["quality_metrics"]["quality_score"]
            if quality_score >= 90:
                report += "✅ EXCELLENT - Data is high quality and ready for analysis\n"
            elif quality_score >= 75:
                report += "✅ GOOD - Data is acceptable for most uses\n"
            elif quality_score >= 50:
                report += "⚠️  MODERATE - Review results before use\n"
            else:
                report += "❌ POOR - Data requires investigation\n"

            return report
        except Exception as e:
            return f"Error generating report: {e}"

    def export_analysis_results(
        self, analysis: Dict[str, Any], output_file: Path
    ) -> None:
        """Export analysis results to JSON file.

        Args:
            analysis: Analysis dictionary
            output_file: Path to output file
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(analysis, f, indent=2, default=str)

        logger.info(f"Analysis exported to {output_file}")
