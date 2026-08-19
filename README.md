# Metro HCM - Weather Data Collector

Automated daily collection of historical weather data for all 14 stations on Ho Chi Minh City Metro Line 1 (Ben Thanh - Suoi Tien).

## Overview

The system fetches yesterday's 24-hour hourly weather data for each metro station using the **OpenWeatherMap Time Machine API (OneCall 3.0)** and commits the results daily via GitHub Actions.

## Stations

| # | Station | Vietnamese | Lat | Lon |
|---|---------|-----------|-----|-----|
| 1 | Ben Thanh | Ben Thanh | 10.7708 | 106.6975 |
| 2 | Opera House | Nha hat TP | 10.7747 | 106.7015 |
| 3 | Ba Son | Ba Son | 10.7815 | 106.7080 |
| 4 | Van Thanh Park | Cong vien Van Thanh | 10.7961 | 106.7155 |
| 5 | Tan Cang | Tan Cang | 10.7986 | 106.7232 |
| 6 | Thao Dien | Thao Dien | 10.8005 | 106.7337 |
| 7 | An Phu | An Phu | 10.8021 | 106.7423 |
| 8 | Rach Chiec | Rach Chiec | 10.8086 | 106.7553 |
| 9 | Phuoc Long | Phuoc Long | 10.8214 | 106.7582 |
| 10 | Binh Thai | Binh Thai | 10.8327 | 106.7639 |
| 11 | Thu Duc | Thu Duc | 10.8464 | 106.7717 |
| 12 | High Tech Park | KCN cao | 10.8590 | 106.7888 |
| 13 | National University | DH Quoc gia | 10.8663 | 106.8012 |
| 14 | Suoi Tien Terminal | Ben xe Suoi Tien | 10.8796 | 106.8141 |

## Data Format

Each station gets a daily CSV file with 24 hourly rows:

| Column | Description |
|--------|-------------|
| `fetched_at` | When the record was fetched |
| `data_timestamp` | Unix timestamp of the observation |
| `datetime` | UTC datetime |
| `datetime_ph` | HCM timezone datetime (UTC+7) |
| `lat`, `lon` | Station coordinates |
| `weather_id`, `weather_main`, `weather_description` | Weather condition |
| `temp`, `feels_like` | Temperature (Celsius) |
| `pressure`, `humidity` | Atmospheric pressure & humidity |
| `visibility` | Visibility in meters |
| `wind_speed`, `wind_direction` | Wind data |
| `clouds_all` | Cloud cover (%) |
| `rain_1h`, `snow_1h` | Precipitation (mm) |

## Usage

### Fetch yesterday's data (default)
```bash
export WEATHER_API_KEY="your_openweathermap_api_key"
python3 fetch_metro_weather.py
```

### Fetch a specific date
```bash
python3 fetch_metro_weather.py --date 2026-08-18
```

### Custom output directory
```bash
python3 fetch_metro_weather.py --output-dir metro_weather
```

## Automated Daily Runs

GitHub Actions runs the fetcher daily at **8:17 AM HCM time** (1:17 AM UTC), after midnight when yesterday's data is available. Results are committed directly to the repository.

To trigger manually: go to **Actions > Fetch Metro Weather > Run workflow**.

## Setup

1. Add your OpenWeatherMap API key as a repository secret named `APP_ID_PROD`
2. The workflow runs automatically on schedule

## Output Structure

```
metros/
  ben_thanh_2026-08-18.csv
  opera_house_2026-08-18.csv
  ...
  suoi_tien_2026-08-18.csv
```

## Requirements

- Python 3.x (no external dependencies, uses only stdlib)
- OpenWeatherMap API key (OneCall 3.0 subscription)
