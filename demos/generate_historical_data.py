#!/usr/bin/env python
"""Generate realistic historical climate data for testing and demos.

Creates synthetic climate data with realistic seasonal patterns,
quality variations, and anomalies for MCP analysis demonstrations.

Usage:
    poetry run python demos/generate_historical_data.py [--years 3] [--stations 20]
"""

import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path


def generate_synthetic_data(
    start_year: int = 2022,
    num_years: int = 1,
    num_stations: int = 12,
    anomaly_months: list = None,
) -> pd.DataFrame:
    """Generate realistic synthetic climate data.

    Args:
        start_year: Starting year for data generation
        num_years: Number of years of data to generate
        num_stations: Number of stations
        anomaly_months: List of months (as strings 'YYYY-MM') with quality issues

    Returns:
        DataFrame with synthetic climate data
    """
    if anomaly_months is None:
        anomaly_months = []

    data = []
    start_date = pd.Timestamp(f"{start_year}-01-01")
    end_date = start_date + pd.DateOffset(years=num_years)

    dates = pd.date_range(start=start_date, end=end_date, freq="D")[:-1]

    for date in dates:
        day_of_year = (date - pd.Timestamp(f"{date.year}-01-01")).days
        month_str = date.strftime("%Y-%m")

        # Seasonal temperature pattern (hemisphere agnostic sine wave)
        base_temp = 15 * np.sin(2 * np.pi * day_of_year / 365)

        for station_idx in range(num_stations):
            station_id = f"SYNTH{date.year}{station_idx:02d}"

            # Add regional variation by station
            regional_offset = (station_idx % 5) * 3 - 6

            # TMAX
            tmax = (
                base_temp
                + regional_offset
                + 10
                + np.random.normal(0, 2)
            )
            data.append(
                {
                    "station_id": station_id,
                    "date": date.strftime("%Y-%m-%d"),
                    "element": "TMAX",
                    "value": round(tmax, 1),
                    "measurement_flag": "",
                    "quality_flag": "",
                    "source_flag": "synthetic",
                }
            )

            # TMIN
            tmin = tmax - 8 - np.random.uniform(0, 4)
            data.append(
                {
                    "station_id": station_id,
                    "date": date.strftime("%Y-%m-%d"),
                    "element": "TMIN",
                    "value": round(tmin, 1),
                    "measurement_flag": "",
                    "quality_flag": "",
                    "source_flag": "synthetic",
                }
            )

            # PRCP with occasional rain
            if np.random.random() > 0.75:
                prcp = np.random.exponential(4)
            else:
                prcp = 0.0

            # Add quality issues for anomaly months
            if month_str in anomaly_months and np.random.random() > 0.8:
                prcp = np.nan

            data.append(
                {
                    "station_id": station_id,
                    "date": date.strftime("%Y-%m-%d"),
                    "element": "PRCP",
                    "value": round(prcp, 1) if not pd.isna(prcp) else np.nan,
                    "measurement_flag": "",
                    "quality_flag": "",
                    "source_flag": "synthetic",
                }
            )

    return pd.DataFrame(data)


def main():
    """Generate and save synthetic climate data."""
    parser = argparse.ArgumentParser(
        description="Generate realistic synthetic climate data for testing"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=1,
        help="Number of years of data to generate (default: 1)",
    )
    parser.add_argument(
        "--stations",
        type=int,
        default=12,
        help="Number of weather stations (default: 12)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Output directory (default: data)",
    )
    parser.add_argument(
        "--split-monthly",
        action="store_true",
        help="Split output into monthly files",
    )

    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Generating Synthetic Climate Data")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Years: {args.years}")
    print(f"  Stations: {args.stations}")
    print(f"  Output: {args.output_dir}")

    # Define anomaly months for demonstration
    anomaly_months = []
    if args.years >= 1:
        # June 2024 will have data quality issues
        anomaly_months.append("2024-06")
    if args.years >= 2:
        # February 2025 will have issues
        anomaly_months.append("2025-02")

    print(f"  Anomaly months (quality issues): {anomaly_months}")

    # Generate data
    print(f"\nGenerating {args.years} year(s) of synthetic data...")
    df = generate_synthetic_data(
        start_year=2024,
        num_years=args.years,
        num_stations=args.stations,
        anomaly_months=anomaly_months,
    )

    print(f"✅ Generated {len(df):,} records")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Stations: {df['station_id'].nunique()}")
    print(f"   Elements: {', '.join(sorted(df['element'].unique()))}")

    if args.split_monthly:
        # Save monthly files
        print(f"\nSaving monthly files...")
        df["year_month"] = pd.to_datetime(df["date"]).dt.to_period("M")
        for period, group in df.groupby("year_month"):
            filename = args.output_dir / f"climate_monthly_{str(period).replace('-', '')}.csv"
            group.drop("year_month", axis=1).to_csv(filename, index=False)
            print(f"  ✅ {filename.name}: {len(group)} records")
    else:
        # Save as single file
        filename = args.output_dir / f"historical_climate_data_{args.years}year.csv"
        df.to_csv(filename, index=False)
        print(f"\n✅ Saved: {filename}")
        print(f"   File size: {filename.stat().st_size / 1024 / 1024:.1f} MB")

    # Print summary statistics
    print(f"\nData Summary:")
    print(f"\nTemperature Statistics (TMAX):")
    tmax = df[df["element"] == "TMAX"]["value"].describe()
    print(f"  Mean: {tmax['mean']:.1f}°C")
    print(f"  Std Dev: {tmax['std']:.1f}°C")
    print(f"  Range: {tmax['min']:.1f}°C to {tmax['max']:.1f}°C")

    print(f"\nTemperature Statistics (TMIN):")
    tmin = df[df["element"] == "TMIN"]["value"].describe()
    print(f"  Mean: {tmin['mean']:.1f}°C")
    print(f"  Std Dev: {tmin['std']:.1f}°C")
    print(f"  Range: {tmin['min']:.1f}°C to {tmin['max']:.1f}°C")

    print(f"\nPrecipitation Statistics (PRCP):")
    prcp = df[df["element"] == "PRCP"]["value"].describe()
    print(f"  Mean: {prcp['mean']:.1f} mm")
    print(f"  Max: {prcp['max']:.1f} mm")
    print(f"  Days with rain: {(df[df['element'] == 'PRCP']['value'] > 0).sum()}")

    print(f"\nData Quality:")
    null_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
    print(f"  Null percentage: {null_pct:.2f}%")
    if null_pct > 5:
        print(f"  ⚠️  Higher null percentage indicates data quality issues in anomaly months")

    print("\n" + "=" * 70)
    print("Next steps:")
    print("  1. Run pipeline on generated data:")
    print(f"     poetry run python -m src run --config config/demo_config.yaml \\")
    print(f"       --data-file {args.output_dir}/climate_monthly_202401.csv")
    print("\n  2. Run MCP analysis:")
    print("     poetry run python -m src mcp report")
    print("\n  3. Run historical trend analysis:")
    print("     poetry run python demos/mcp_historical_analysis.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
