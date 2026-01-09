#!/usr/bin/env python
"""Explore and document real climate data sources (not synthetic).

This script helps identify and test actual NOAA and other sources
for real historical climate data that can be used with the pipeline.

Usage:
    poetry run python helper_scripts/explore_real_data_sources.py
"""

import requests
from datetime import datetime, timedelta
import json
from pathlib import Path


def test_noaa_weather_gov_api():
    """Test NOAA Weather.gov API for current conditions."""
    print("\n1. NOAA Weather.gov API (US Data, No Auth Required)")
    print("-" * 70)

    # Get a sample grid point (San Francisco area)
    try:
        # First get grid point metadata
        lat, lon = 37.7749, -122.4194  # San Francisco
        points_url = f"https://api.weather.gov/points/{lat},{lon}"

        print(f"Testing NOAA API with point: {lat}, {lon} (San Francisco)")
        response = requests.get(points_url, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if "properties" in data:
                print(f"✅ API accessible")
                print(f"   Grid Point: {data['properties'].get('gridPoint')}")
                print(f"   Forecast URL: {data['properties'].get('forecast')}")
                print(
                    f"   Forecast Grid Data: {data['properties'].get('forecastGridData')}"
                )
        else:
            print(f"⚠️  Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("""
⚠️  Limitation: Weather.gov API only has ~7 days of historical data
     (mainly for current/future forecasts)
""")


def document_ghcn_daily():
    """Document NOAA GHCN-Daily archive."""
    print("\n2. NOAA GHCN-Daily FTP Archive (Real Historical Data)")
    print("-" * 70)
    print("""
✅ What it is:
   - Global Historical Climatology Network - Daily (GHCN-Daily)
   - 20,000+ weather stations worldwide
   - Daily data going back 100+ years (1800s-present)
   - Temperature, precipitation, snow, wind, etc.
   - FREE and PUBLIC

✅ Data available:
   - By station (all-in-one files)
   - By year
   - Pre-compiled datasets

✅ Access methods:
   A. FTP: ftp://ftp.ncei.noaa.gov/pub/data/ghcn/daily/
   B. Web: https://www.ncei.noaa.gov/data/ghcn-daily/
   C. Direct download: https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/all/

✅ Format:
   - Fixed-width text files
   - Daily observations
   - Quality flags included
   - Documented: https://www.ncei.noaa.gov/products/land-based-station-observations/global-historical-climatology-network-daily

✅ Popular Stations:
   - USW00023234 (New York Central Park)
   - USW00093134 (Los Angeles International)
   - CAN00049999 (Toronto, Canada)
   - AUM00035012 (Sydney, Australia)

✅ How to find station IDs:
   - Browse: https://www.ncei.noaa.gov/products/land-based-station-observations/global-historical-climatology-network-daily
   - Use ghcn-daily.csv from FTP
   - Search by location name
""")


def document_isd_lite():
    """Document NOAA ISD-Lite."""
    print("\n3. NOAA ISD-Lite (Integrated Surface Database)")
    print("-" * 70)
    print("""
✅ What it is:
   - Simplified version of full ISD data
   - ~2,200 stations
   - 1901-present
   - Temperature, precipitation, wind
   - Smaller files than GHCN-Daily

Access: ftp://ftp.ncei.noaa.gov/pub/data/noaa/

✅ Stations:
   - Fewer than GHCN but easier to work with
   - Better quality control
   - Uniform format
""")


def document_cdo_web():
    """Document NOAA CDO Web interface."""
    print("\n4. NOAA CDO (Climate Data Online) - Web Interface")
    print("-" * 70)
    print("""
✅ Web interface:
   https://www.ncei.noaa.gov/cdo-web/

✅ Features:
   - Search by location
   - Download custom date ranges
   - Requires free registration
   - Easy for one-off queries
   - Can export to CSV

⚠️  Limitation: API has request limits (1200 req/day for registered users)

✅ Usage:
   1. Go to https://www.ncei.noaa.gov/cdo-web/
   2. Click "Select" -> Choose a dataset (Daily Summaries, etc.)
   3. Search for location
   4. Select date range
   5. Download as CSV
""")


def document_open_meteo():
    """Document Open-Meteo alternative."""
    print("\n5. Open-Meteo (Alternative - Free Historical Weather Data)")
    print("-" * 70)
    print("""
✅ What it is:
   - Free historical weather data API
   - Global coverage
   - No API key required
   - Archive: 1940-present

✅ Coverage:
   - Temperature min/max
   - Precipitation
   - Wind speed
   - Relative humidity
   - Sunrise/sunset

✅ Access: https://open-meteo.com/

✅ Python usage:
   import requests
   url = "https://archive-api.open-meteo.com/v1/archive"
   params = {
       "latitude": 40.7128,
       "longitude": -74.0060,
       "start_date": "2024-01-01",
       "end_date": "2024-12-31",
       "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
       "timezone": "auto"
   }
   response = requests.get(url, params=params)
   data = response.json()

✅ Advantages:
   - Super easy (no auth, no parsing)
   - JSON response
   - Global coverage
   - Good for quick demos

⚠️  Trade-off: Slightly less precise than NOAA for certain regions
""")


def print_recommendation():
    """Print final recommendation."""
    print("\n" + "=" * 70)
    print("RECOMMENDATION FOR YOUR PROJECT")
    print("=" * 70)
    print("""
BEST OPTION: NOAA GHCN-Daily

Why:
  ✅ Used by IPCC climate studies
  ✅ Real weather station data (not interpolated)
  ✅ 100+ years of history available
  ✅ Professional standard in climate science
  ✅ Your Quilt demo will use REAL production data
  ✅ Perfect for consulting story: "Real data, not simulated"

HOW TO GET GHCN-DAILY DATA:

Option A - Direct FTP Download (Easiest):
  1. Go to: https://www.ncei.noaa.gov/data/ghcn-daily/
  2. Navigate to "access/" folder
  3. Find station by name or ID
  4. Download .csv file for that station
  5. Use with pipeline: poetry run python -m src run --config config/demo_config.yaml --data-file downloaded_data.csv

Option B - Programmatic (Python):
  See fetch_ghcn_daily_data.py script

Option C - Web UI (Simplest):
  1. Go to: https://www.ncei.noaa.gov/cdo-web/
  2. Select dataset and location
  3. Download CSV
  4. Done!

ALTERNATIVE: Open-Meteo (If NOAA is slow)
  - Faster
  - Requires no signup
  - See fetch_open_meteo_data.py script

NEXT STEPS:
  1. Decide on station (e.g., NYC, SF, Toronto)
  2. Decide on timeframe (1 year recommended for demos)
  3. Run fetch script to download
  4. Use with pipeline for real analysis
""")


def print_next_scripts():
    """Show what scripts to create next."""
    print("\n" + "=" * 70)
    print("NEXT SCRIPTS TO CREATE")
    print("=" * 70)
    print("""
1. fetch_ghcn_daily_data.py
   - Downloads GHCN-Daily data for specified station
   - Converts to our pipeline format
   - Handles station ID lookup

2. fetch_open_meteo_data.py
   - Downloads from Open-Meteo API
   - Much simpler/faster
   - Good backup option

3. find_ghcn_stations.py
   - Search GHCN station list
   - Find by location/name
   - Show available stations

These will be in: helper_scripts/
""")


def main():
    """Run all documentation."""
    print("\n" + "=" * 70)
    print("REAL CLIMATE DATA SOURCES - EXPLORATION")
    print("=" * 70)

    test_noaa_weather_gov_api()
    document_ghcn_daily()
    document_isd_lite()
    document_cdo_web()
    document_open_meteo()
    print_recommendation()
    print_next_scripts()

    print("\n" + "=" * 70)
    print("STATUS")
    print("=" * 70)
    print("""
✅ Explored 5 real data sources
✅ GHCN-Daily identified as best option
✅ Ready to fetch real data

Next: Run fetch_ghcn_daily_data.py or fetch_open_meteo_data.py
to download actual historical climate data.
""")


if __name__ == "__main__":
    main()
