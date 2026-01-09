#!/usr/bin/env python
"""Fetch real historical weather data from Open-Meteo API.

Open-Meteo provides free, global historical weather data without
API keys. This script downloads data for a location and converts it
to our pipeline's expected format.

Usage:
    poetry run python helper_scripts/fetch_open_meteo_data.py \\
      --lat 40.7128 --lon -74.0060 \\
      --start-date 2023-01-01 --end-date 2024-12-31 \\
      --location "New York City"

    poetry run python helper_scripts/fetch_open_meteo_data.py \\
      --lat 51.5074 --lon -0.1278 \\
      --start-date 2024-01-01 --end-date 2024-12-31 \\
      --location "London"
"""

import argparse
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime


def fetch_open_meteo_data(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    location_name: str = "Location",
) -> pd.DataFrame:
    """Fetch historical weather data from Open-Meteo API.

    Args:
        latitude: Location latitude
        longitude: Location longitude
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        location_name: Name of location (for station_id)

    Returns:
        DataFrame with weather data in pipeline format
    """
    print(f"\nFetching data from Open-Meteo API...")
    print(f"  Location: {location_name} ({latitude}, {longitude})")
    print(f"  Date range: {start_date} to {end_date}")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "temperature_unit": "celsius",
        "precipitation_unit": "mm",
        "timezone": "auto",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    print(f"✅ Data retrieved")

    # Convert to pipeline format
    daily_data = data["daily"]
    dates = daily_data["time"]
    tmax = daily_data["temperature_2m_max"]
    tmin = daily_data["temperature_2m_min"]
    prcp = daily_data["precipitation_sum"]

    # Create station ID
    station_id = f"OPEN{latitude:.2f}_{longitude:.2f}".replace(".", "").replace(
        "-", "N"
    )

    records = []

    for date, temp_max, temp_min, precip in zip(dates, tmax, tmin, prcp):
        # TMAX
        if temp_max is not None:
            records.append(
                {
                    "station_id": station_id,
                    "date": date,
                    "element": "TMAX",
                    "value": round(float(temp_max), 1),
                    "measurement_flag": "",
                    "quality_flag": "",
                    "source_flag": "open-meteo",
                }
            )

        # TMIN
        if temp_min is not None:
            records.append(
                {
                    "station_id": station_id,
                    "date": date,
                    "element": "TMIN",
                    "value": round(float(temp_min), 1),
                    "measurement_flag": "",
                    "quality_flag": "",
                    "source_flag": "open-meteo",
                }
            )

        # PRCP
        if precip is not None:
            records.append(
                {
                    "station_id": station_id,
                    "date": date,
                    "element": "PRCP",
                    "value": round(float(precip), 1),
                    "measurement_flag": "",
                    "quality_flag": "",
                    "source_flag": "open-meteo",
                }
            )

    df = pd.DataFrame(records)

    print(f"\n✅ Data converted to pipeline format")
    print(f"   Records: {len(df):,}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Station ID: {station_id}")
    print(f"   Elements: {', '.join(sorted(df['element'].unique()))}")

    return df


def main():
    """Fetch and save Open-Meteo data."""
    parser = argparse.ArgumentParser(
        description="Fetch real historical weather data from Open-Meteo API"
    )
    parser.add_argument(
        "--lat",
        type=float,
        required=True,
        help="Latitude of location",
    )
    parser.add_argument(
        "--lon",
        type=float,
        required=True,
        help="Longitude of location",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--location",
        type=str,
        default="Location",
        help="Location name (for reference)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/real_weather_data.csv"),
        help="Output file path",
    )

    args = parser.parse_args()

    try:
        # Fetch data
        df = fetch_open_meteo_data(
            args.lat,
            args.lon,
            args.start_date,
            args.end_date,
            args.location,
        )

        # Save to file
        args.output.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(args.output, index=False)

        print(f"\n✅ Saved to: {args.output}")
        print(f"\nData summary:")

        # Temperature stats
        tmax = df[df["element"] == "TMAX"]["value"]
        tmin = df[df["element"] == "TMIN"]["value"]
        prcp = df[df["element"] == "PRCP"]["value"]

        print(f"\nTemperature (TMAX):")
        print(f"  Min: {tmax.min():.1f}°C")
        print(f"  Max: {tmax.max():.1f}°C")
        print(f"  Mean: {tmax.mean():.1f}°C")

        print(f"\nTemperature (TMIN):")
        print(f"  Min: {tmin.min():.1f}°C")
        print(f"  Max: {tmax.max():.1f}°C")
        print(f"  Mean: {tmin.mean():.1f}°C")

        print(f"\nPrecipitation (PRCP):")
        print(f"  Mean: {prcp.mean():.1f} mm/day")
        print(f"  Max: {prcp.max():.1f} mm")
        rainy_days = (prcp > 0).sum()
        print(f"  Days with rain: {rainy_days} ({100*rainy_days/len(prcp):.1f}%)")

        print(f"\n✅ Ready to use with pipeline:")
        print(f"   poetry run python -m src run --config config/demo_config.yaml \\")
        print(f"     --data-file {args.output}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
