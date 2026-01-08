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
