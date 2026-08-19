#!/usr/bin/env python3
"""
Fetch historical weather data for HCM Metro Line 1 stations.

Runs daily to get yesterday's 24-hour weather data for all 14 stations.
Output: one CSV per station in metro_weather/ directory.

Usage:
    python3 fetch_metro_weather.py                  # Fetch yesterday's data
    python3 fetch_metro_weather.py --date 2026-08-18  # Fetch specific date
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

# HCM Metro Line 1 stations
METRO_STATIONS = [
    {"id": "ben_thanh", "name": "Ben Thanh", "name_vi": "Bến Thành", "lat": 10.7708, "lon": 106.6975},
    {"id": "opera_house", "name": "Opera House", "name_vi": "Nhà hát TP", "lat": 10.7747, "lon": 106.7015},
    {"id": "ba_son", "name": "Ba Son", "name_vi": "Ba Son", "lat": 10.7815, "lon": 106.7080},
    {"id": "van_thanh_park", "name": "Van Thanh Park", "name_vi": "Công viên Văn Thánh", "lat": 10.7961, "lon": 106.7155},
    {"id": "tan_cang", "name": "Tan Cang", "name_vi": "Tân Cảng", "lat": 10.7986, "lon": 106.7232},
    {"id": "thao_dien", "name": "Thao Dien", "name_vi": "Thảo Điền", "lat": 10.8005, "lon": 106.7337},
    {"id": "an_phu", "name": "An Phu", "name_vi": "An Phú", "lat": 10.8021, "lon": 106.7423},
    {"id": "rach_chiec", "name": "Rach Chiec", "name_vi": "Rạch Chiếc", "lat": 10.8086, "lon": 106.7553},
    {"id": "phuoc_long", "name": "Phuoc Long", "name_vi": "Phước Long", "lat": 10.8214, "lon": 106.7582},
    {"id": "binh_thai", "name": "Binh Thai", "name_vi": "Bình Thái", "lat": 10.8327, "lon": 106.7639},
    {"id": "thu_duc", "name": "Thu Duc", "name_vi": "Thủ Đức", "lat": 10.8464, "lon": 106.7717},
    {"id": "high_tech_park", "name": "High Tech Park", "name_vi": "KCN cao", "lat": 10.8590, "lon": 106.7888},
    {"id": "national_university", "name": "National University", "name_vi": "ĐH Quốc gia", "lat": 10.8663, "lon": 106.8012},
    {"id": "suoi_tien", "name": "Suoi Tien Terminal", "name_vi": "Bến xe Suối Tiên", "lat": 10.8796, "lon": 106.8141},
]

HCM_TZ = timezone(timedelta(hours=7))


def fetch_hourly_data(lat, lon, unix_ts, api_key):
    """Fetch weather data for a specific hour from OpenWeatherMap Time Machine API."""
    api_url = (
        f"https://api.openweathermap.org/data/3.0/onecall/timemachine"
        f"?lat={lat}&lon={lon}&dt={unix_ts}&units=metric&appid={api_key}"
    )

    try:
        with urlopen(api_url) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        print(f"    HTTP Error {e.code}: {e.reason}")
        return None
    except URLError as e:
        print(f"    Error: {e}")
        return None


def extract_weather_fields(hourly_point, lat, lon, fetched_at):
    """Extract weather fields matching the existing policy CSV format."""
    rain = hourly_point.get("rain", {})
    rain_1h = rain.get("1h") if isinstance(rain, dict) else None
    snow = hourly_point.get("snow", {})
    snow_1h = snow.get("1h") if isinstance(snow, dict) else None

    return {
        "fetched_at": fetched_at,
        "data_timestamp": hourly_point.get("dt"),
        "datetime": datetime.fromtimestamp(hourly_point.get("dt", 0), tz=timezone.utc).isoformat() if hourly_point.get("dt") else "",
        "datetime_ph": datetime.fromtimestamp(hourly_point.get("dt", 0), tz=HCM_TZ).isoformat() if hourly_point.get("dt") else "",
        "lat": lat,
        "lon": lon,
        "timezone": "Asia/Ho_Chi_Minh",
        "weather_id": hourly_point.get("weather", [{}])[0].get("id", ""),
        "weather_main": hourly_point.get("weather", [{}])[0].get("main", ""),
        "weather_description": hourly_point.get("weather", [{}])[0].get("description", ""),
        "temp": hourly_point.get("temp"),
        "feels_like": hourly_point.get("feels_like"),
        "temp_min": "",
        "temp_max": "",
        "pressure": hourly_point.get("pressure"),
        "humidity": hourly_point.get("humidity"),
        "sea_level_pressure": hourly_point.get("sea_level"),
        "grnd_level_pressure": hourly_point.get("grnd_level"),
        "visibility": hourly_point.get("visibility"),
        "wind_speed": hourly_point.get("wind_speed"),
        "wind_direction": hourly_point.get("wind_deg"),
        "clouds_all": hourly_point.get("clouds"),
        "sunrise": hourly_point.get("sunrise"),
        "sunset": hourly_point.get("sunset"),
        "rain_1h": rain_1h,
        "snow_1h": snow_1h,
    }


def fetch_station_day(station, target_date, api_key):
    """Fetch 24 hours of weather data for one station on a given date."""
    # Build 24 timestamps: 0h to 23h in HCM time, converted to UTC
    day_start_hcm = datetime.combine(target_date, datetime.min.time(), tzinfo=HCM_TZ)
    day_start_utc = day_start_hcm.astimezone(timezone.utc)

    rows = []
    fetched_at = datetime.now(HCM_TZ).isoformat()
    for hour_offset in range(24):
        dt_utc = day_start_utc + timedelta(hours=hour_offset)
        ts = int(dt_utc.timestamp())

        data = fetch_hourly_data(station["lat"], station["lon"], ts, api_key)
        if not data:
            continue

        hourly = data.get("hourly") or data.get("data", [])
        if not hourly:
            continue

        h = hourly[0]
        fields = extract_weather_fields(h, station["lat"], station["lon"], fetched_at)
        rows.append(fields)

        # Rate limit: small delay between calls
        time.sleep(0.3)

    return rows


def save_station_csv(station, rows, output_dir, target_date):
    """Save weather data to a per-station CSV file."""
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, f"{station['id']}_{target_date}.csv")

    fieldnames = [
        "fetched_at", "data_timestamp", "datetime", "datetime_ph",
        "lat", "lon", "timezone",
        "weather_id", "weather_main", "weather_description",
        "temp", "feels_like", "temp_min", "temp_max",
        "pressure", "humidity", "sea_level_pressure", "grnd_level_pressure",
        "visibility", "wind_speed", "wind_direction", "clouds_all",
        "sunrise", "sunset", "rain_1h", "snow_1h",
    ]

    # If file exists, load existing timestamps to avoid duplicates
    existing_ts = set()
    if os.path.exists(csv_path):
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_ts.add(row.get("data_timestamp"))

    # Append new rows (skip duplicates)
    new_rows = [r for r in rows if str(r["data_timestamp"]) not in existing_ts]

    if not new_rows:
        print(f"    No new data to write (all {len(rows)} rows already exist)")
        return csv_path

    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(new_rows)

    print(f"    Wrote {len(new_rows)} new rows to {csv_path}")
    return csv_path


def main():
    parser = argparse.ArgumentParser(description="Fetch HCM Metro weather data")
    parser.add_argument("--date", type=str, help="Date to fetch (YYYY-MM-DD), default: yesterday HCM time")
    parser.add_argument("--output-dir", type=str, default="metros", help="Output directory (default: metros)")
    args = parser.parse_args()

    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        print("Error: Set WEATHER_API_KEY environment variable")
        sys.exit(1)

    # Determine target date
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        now_hcm = datetime.now(HCM_TZ)
        target_date = (now_hcm - timedelta(days=1)).date()

    print(f"=" * 60)
    print(f"HCM METRO WEATHER FETCHER")
    print(f"=" * 60)
    print(f"Target date: {target_date} (HCM time)")
    print(f"Stations: {len(METRO_STATIONS)}")
    print(f"Output: {args.output_dir}/")
    print()

    success = []
    failed = []

    for i, station in enumerate(METRO_STATIONS, 1):
        print(f"[{i}/{len(METRO_STATIONS)}] {station['name']} ({station['name_vi']})")
        try:
            rows = fetch_station_day(station, target_date, api_key)
            if rows:
                save_station_csv(station, rows, args.output_dir, target_date)
                success.append(station["name"])
            else:
                print(f"    No data returned")
                failed.append(station["name"])
        except Exception as e:
            print(f"    Error: {e}")
            failed.append(station["name"])

    # Summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY - {target_date}")
    print(f"{'=' * 60}")
    print(f"Success: {len(success)}/{len(METRO_STATIONS)}")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    print(f"Output dir: {args.output_dir}/")


if __name__ == "__main__":
    main()
