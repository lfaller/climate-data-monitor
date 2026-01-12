"""CLI entry point for the climate data monitor pipeline.

Usage:
    python -m src run --config config/demo_config.yaml
    python -m src run --config config/production_config.yaml --push
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

from .orchestrator import PipelineOrchestrator


def setup_logging(config: dict) -> None:
    """Set up logging based on configuration.

    Args:
        config: Configuration dictionary with logging section
    """
    logging_config = config.get("logging", {})
    level = logging.getLevelName(logging_config.get("level", "INFO"))
    log_dir = Path(logging_config.get("log_dir", "logs"))

    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers = []

    if logging_config.get("console_logging", True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(format_str))
        handlers.append(console_handler)

    if logging_config.get("file_logging", True):
        log_file = log_dir / "pipeline.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_str))
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers)


def load_config(config_file: Path) -> dict:
    """Load configuration from YAML file.

    Args:
        config_file: Path to YAML config file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    with open(config_file) as f:
        config = yaml.safe_load(f)

    return config


def validate_config(config: dict) -> None:
    """Validate required configuration sections.

    Args:
        config: Configuration dictionary

    Raises:
        ValueError: If required sections are missing
    """
    required_sections = ["climate", "quality", "quilt"]
    missing = [s for s in required_sections if s not in config]

    if missing:
        raise ValueError(f"Missing required config sections: {missing}")


def run_pipeline(args) -> int:
    """Run the complete climate data monitoring pipeline.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Load configuration
        config = load_config(args.config)
        validate_config(config)

        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)

        logger.info(f"Loading configuration from {args.config}")

        # Override push_to_registry if --push flag is set
        if args.push:
            config["quilt"]["push_to_registry"] = True
            logger.info("Enabling push to S3 registry (--push flag)")

        # Create and run orchestrator
        orchestrator = PipelineOrchestrator(config)
        results = orchestrator.run(args.data_file)

        # Print status report
        report = orchestrator.get_status_report(results)
        print(report)

        # Save detailed results
        if args.output:
            results_file = Path(args.output)
            results_file.parent.mkdir(parents=True, exist_ok=True)
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Detailed results saved to {results_file}")

        return 0 if results["success"] else 1

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        logging.exception("Pipeline execution failed")
        return 1


def analyze_package(args) -> int:
    """Analyze a Quilt package.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        from .quilt_analyzer import QuiltPackageAnalyzer

        analyzer = QuiltPackageAnalyzer(args.package, registry=args.registry)
        analyzer.print_summary()

        # Export metadata if requested
        if args.export_metadata:
            analyzer.export_metadata_to_json(args.export_metadata)

        # Export data if requested
        if args.export_data:
            analyzer.export_data_to_csv(args.export_data)

        return 0

    except Exception as e:
        print(f"ERROR: Failed to analyze package: {e}", file=sys.stderr)
        return 1


def mcp_query(args) -> int:
    """Execute MCP-style queries on climate packages (AI-friendly).

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code
    """
    try:
        from .mcp_analyzer import MCPClimateAnalyzer

        analyzer = MCPClimateAnalyzer()

        # Route to appropriate query type
        if args.query_type == "search":
            results = analyzer.search_packages(
                quality_threshold=args.quality_threshold,
                element_filter=args.elements,
            )
            print(json.dumps(results, indent=2, default=str))

        elif args.query_type == "metrics":
            metrics = analyzer.get_package_metrics(args.package)
            print(json.dumps(metrics, indent=2, default=str))

        elif args.query_type == "compare":
            if not args.compare_with:
                print("ERROR: --compare-with required for 'compare' query", file=sys.stderr)
                return 1
            comparison = analyzer.compare_packages(args.package, args.compare_with)
            print(json.dumps(comparison, indent=2, default=str))

        elif args.query_type == "sample":
            sample = analyzer.get_data_sample(args.package, limit=args.limit)
            print(json.dumps(sample, indent=2, default=str))

        elif args.query_type == "temperature":
            analysis = analyzer.analyze_temperature_trends(args.package)
            print(json.dumps(analysis, indent=2, default=str))

        elif args.query_type == "completeness":
            completeness = analyzer.analyze_data_completeness(args.package)
            print(json.dumps(completeness, indent=2, default=str))

        elif args.query_type == "report":
            report = analyzer.generate_summary_report(args.package)
            print(report)

        return 0

    except Exception as e:
        print(f"ERROR: MCP query failed: {e}", file=sys.stderr)
        logging.exception("MCP query error")
        return 1


def main() -> int:
    """Main entry point for CLI.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Climate Data Monitor - Automated quality monitoring and versioning"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run the complete pipeline")
    run_parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to YAML configuration file",
    )
    run_parser.add_argument(
        "--data-file",
        type=Path,
        default=None,
        help="Optional path to input data file (overrides config source_url)",
    )
    run_parser.add_argument(
        "--push",
        action="store_true",
        help="Enable push to S3 registry (overrides config setting)",
    )
    run_parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Save detailed results to JSON file",
    )
    run_parser.set_defaults(func=run_pipeline)

    # 'analyze' subcommand
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a Quilt package")
    analyze_parser.add_argument(
        "package",
        help="Package name to analyze (e.g., climate/demo-sample)",
    )
    analyze_parser.add_argument(
        "--registry",
        type=str,
        default=None,
        help="Quilt registry URL (e.g., s3://my-bucket). If not provided, uses local registry",
    )
    analyze_parser.add_argument(
        "--export-metadata",
        type=Path,
        default=None,
        help="Export metadata to JSON file",
    )
    analyze_parser.add_argument(
        "--export-data",
        type=Path,
        default=None,
        help="Export data to CSV file",
    )
    analyze_parser.set_defaults(func=analyze_package)

    # 'mcp' subcommand for AI-friendly queries
    mcp_parser = subparsers.add_parser(
        "mcp",
        help="Execute MCP-style queries (AI-friendly analysis)",
    )
    mcp_parser.add_argument(
        "query_type",
        choices=[
            "search",
            "metrics",
            "compare",
            "sample",
            "temperature",
            "completeness",
            "report",
        ],
        help="Type of query to execute",
    )
    mcp_parser.add_argument(
        "--package",
        default="climate/demo-sample",
        help="Package to query (default: climate/demo-sample)",
    )
    mcp_parser.add_argument(
        "--quality-threshold",
        type=float,
        default=None,
        help="For 'search': minimum quality score (0-100)",
    )
    mcp_parser.add_argument(
        "--elements",
        nargs="+",
        default=None,
        help="For 'search': filter by climate elements (TMAX TMIN PRCP etc)",
    )
    mcp_parser.add_argument(
        "--compare-with",
        default=None,
        help="For 'compare': second package to compare with",
    )
    mcp_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="For 'sample': number of rows to return (default: 10)",
    )
    mcp_parser.set_defaults(func=mcp_query)

    # Parse arguments
    args = parser.parse_args()

    # If no command specified, print help
    if not args.command:
        parser.print_help()
        return 0

    # Execute command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
