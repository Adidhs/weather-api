import json
import requests
import time
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def weather_condition(code):
    conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Light snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Light rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Light snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with light hail",
        99: "Thunderstorm with heavy hail"
    }

    return conditions.get(code, "Unknown")


# ============================================================
# START TOTAL PIPELINE TIMER
# ============================================================

formatter_start = time.time()


# ============================================================
# READ OPEN-METEO RAW DATA
# ============================================================

with open("weather_raw.json", "r") as file:
    data = json.load(file)

with open("imd_warning.json", "r") as file:
    imd_warning = json.load(file)

current = data["current"]
collection_metadata = data["collection_metadata"]


# ============================================================
# CALCULATE OBSERVATION AGE
# ============================================================

timezone = ZoneInfo(data["timezone"])

observation_time = datetime.fromisoformat(
    current["time"]
).replace(tzinfo=timezone)

now = datetime.now(timezone)

observation_age_seconds = round(
    (now - observation_time).total_seconds()
)


# ============================================================
# GET GFS DATA
# ============================================================

gfs_url = "https://api.open-meteo.com/v1/gfs"

gfs_params = {
    "latitude": 20.2961,
    "longitude": 85.8245,
    "hourly": "temperature_2m,precipitation,wind_speed_10m",
    "daily": "temperature_2m_max,precipitation_sum,wind_speed_10m_max",
    "timezone": "Asia/Kolkata"
}

gfs_start = time.time()

gfs_response = requests.get(
    gfs_url,
    params=gfs_params,
    timeout=30
)

gfs_end = time.time()

gfs_latency = round(gfs_end - gfs_start, 3)

print("GFS Status:", gfs_response.status_code)

if gfs_response.status_code != 200:
    print("GFS Error:", gfs_response.text)
    raise SystemExit("GFS request failed.")

gfs_data = gfs_response.json()


# ============================================================
# EXTRACT GFS DAILY VALUES
# ============================================================

gfs_daily = gfs_data["daily"]

gfs_forecast = {
    "temperature_max_c": gfs_daily["temperature_2m_max"][0],
    "rainfall_24h_mm": gfs_daily["precipitation_sum"][0],
    "wind_max_kmh": gfs_daily["wind_speed_10m_max"][0]
}


# ============================================================
# GET WEATHERAPI DATA
# ============================================================

weatherapi_url = "https://api.weatherapi.com/v1/current.json"

weatherapi_key = os.getenv("WEATHER_API_KEY")

if not weatherapi_key:
    raise SystemExit(
        "WEATHER_API_KEY is not set in the current terminal."
    )

weatherapi_params = {
    "key": weatherapi_key,
    "q": "20.2961,85.8245"
}

weatherapi_start = time.time()

weatherapi_response = requests.get(
    weatherapi_url,
    params=weatherapi_params,
    timeout=30
)

weatherapi_end = time.time()

weatherapi_latency = round(
    weatherapi_end - weatherapi_start, 3
)

print("WeatherAPI Status:", weatherapi_response.status_code)

if weatherapi_response.status_code != 200:
    print("WeatherAPI Error:", weatherapi_response.text)
    raise SystemExit("WeatherAPI request failed.")

weatherapi_data = weatherapi_response.json()


# ============================================================
# EXTRACT WEATHERAPI CURRENT DATA
# ============================================================

weatherapi_current = weatherapi_data["current"]

weatherapi_values = {
    "temperature_c": weatherapi_current["temp_c"],
    "humidity_pct": weatherapi_current["humidity"],
    "pressure_hpa": weatherapi_current["pressure_mb"],
    "wind_speed_kmh": weatherapi_current["wind_kph"],
    "wind_direction_deg": weatherapi_current["wind_degree"],
    "precipitation_mm": weatherapi_current["precip_mm"],
    "cloud_cover_pct": weatherapi_current["cloud"],
    "feels_like_c": weatherapi_current["feelslike_c"],
    "visibility_km": weatherapi_current["vis_km"],
    "uv_index": weatherapi_current["uv"]
}


# ============================================================
# GET AIR QUALITY DATA
# ============================================================

air_quality_url = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
)

air_quality_params = {
    "latitude": 20.2961,
    "longitude": 85.8245,
    "current": (
        "european_aqi,"
        "pm2_5,"
        "pm10,"
        "nitrogen_dioxide,"
        "ozone"
    ),
    "timezone": "Asia/Kolkata"
}

air_quality_start = time.time()

air_quality_response = requests.get(
    air_quality_url,
    params=air_quality_params,
    timeout=30
)

air_quality_end = time.time()

air_quality_latency = round(
    air_quality_end - air_quality_start, 3
)

print(
    "Air Quality Status:",
    air_quality_response.status_code
)

if air_quality_response.status_code != 200:
    print(
        "Air Quality Error:",
        air_quality_response.text
    )
    raise SystemExit("Air Quality request failed.")

air_quality_data = air_quality_response.json()


# ============================================================
# EXTRACT AIR QUALITY VALUES
# ============================================================

air_quality_current = air_quality_data["current"]

air_quality_values = {
    "aqi": air_quality_current["european_aqi"],
    "aqi_standard": "European AQI",
    "pm25_ug_m3": air_quality_current["pm2_5"],
    "pm10_ug_m3": air_quality_current["pm10"],
    "no2_ug_m3": air_quality_current["nitrogen_dioxide"],
    "o3_ug_m3": air_quality_current["ozone"],
    "source": "Open-Meteo Air Quality"
}


# ============================================================
# HOURLY FORECAST
# ============================================================

hourly = data["hourly"]


# ============================================================
# CALCULATE ACCUMULATED RAINFALL
# ============================================================

current_time = datetime.fromisoformat(current["time"])

hourly_times = [
    datetime.fromisoformat(t)
    for t in hourly["time"]
]

current_index = min(
    range(len(hourly_times)),
    key=lambda i: abs(
        hourly_times[i] - current_time
    )
)

precipitation = hourly["precipitation"]

rain_1h = sum(
    precipitation[
        max(0, current_index):
        current_index + 1
    ]
)

rain_3h = sum(
    precipitation[
        max(0, current_index - 2):
        current_index + 1
    ]
)

rain_6h = sum(
    precipitation[
        max(0, current_index - 5):
        current_index + 1
    ]
)

rain_24h = sum(
    precipitation[
        max(0, current_index - 23):
        current_index + 1
    ]
)


# ============================================================
# BUILD HOURLY FORECAST
# ============================================================

hourly_forecast = []

for i in range(len(hourly["time"])):

    hourly_forecast.append({
        "timestamp": hourly["time"][i],
        "temperature_c": hourly["temperature_2m"][i],
        "humidity_pct": hourly["relative_humidity_2m"][i],
        "precipitation_mm": hourly["precipitation"][i],
        "rain_probability_pct":
            hourly["precipitation_probability"][i],
        "wind_speed_kmh":
            hourly["wind_speed_10m"][i],
        "wind_gust_kmh":
            hourly["wind_gusts_10m"][i],
        "wind_direction_deg":
            hourly["wind_direction_10m"][i],
        "cloud_cover_pct":
            hourly["cloud_cover"][i],
        "visibility_km":
            hourly["visibility"][i] / 1000,
        "dew_point_c":
            hourly["dew_point_2m"][i],
        "weather_code":
            hourly["weather_code"][i],
        "weather_condition":
            weather_condition(
                hourly["weather_code"][i]
            )
    })


# ============================================================
# DAILY FORECAST
# ============================================================

daily = data["daily"]

daily_forecast = []

for i in range(len(daily["time"])):

    daily_forecast.append({
        "date": daily["time"][i],

        "temperature": {
            "min_c": daily["temperature_2m_min"][i],
            "max_c": daily["temperature_2m_max"][i]
        },

        "rain_probability_pct":
            daily["precipitation_probability_max"][i],

        "precipitation_mm":
            daily["precipitation_sum"][i],

        "wind": {
            "max_speed_kmh":
                daily["wind_speed_10m_max"][i],
            "max_gust_kmh":
                daily["wind_gusts_10m_max"][i],
            "dominant_direction_deg":
                daily["wind_direction_10m_dominant"][i]
        },

        "uv_index_max":
            daily["uv_index_max"][i],

        "weather_code":
            daily["weather_code"][i],

        "weather_condition":
            weather_condition(
                daily["weather_code"][i]
            )
    })


# ============================================================
# CALCULATE TOTAL PROCESSING / PIPELINE LATENCY
# ============================================================

formatter_end = time.time()

latency_seconds = round(
    formatter_end - formatter_start, 3
)


# ============================================================
# CREATE STANDARDIZED JSON
# ============================================================

standardized_data = {

    "location": {
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "city": "Bhubaneswar",
        "district": "Khordha",
        "state": "Odisha",
        "country": "India",
        "timezone": data["timezone"],
        "elevation_m": data["elevation"]
    },

    "metadata": {
        "generated_at": current["time"],
        "source": collection_metadata["source"],
        "source_type": "observation",
        "retrieved_at": collection_metadata["retrieved_at"],
        "request_latency_seconds":
            collection_metadata["request_latency_seconds"]
    },

    "sources": {
        "weather_forecast": "Open-Meteo",
        "nwp_model": "GFS",
        "current_weather_comparison": "WeatherAPI",
        "official_warning": "IMD",
        "air_quality": "Open-Meteo Air Quality"
    },

    "current_weather": {

        "temperature": {
            "value": current["temperature_2m"],
            "unit": "C"
        },

        "feels_like": {
            "value": current["apparent_temperature"],
            "unit": "C"
        },

        "humidity": {
            "value": current["relative_humidity_2m"],
            "unit": "%"
        },

        "pressure": {
            "value": current["pressure_msl"],
            "unit": "hPa"
        },

        "wind": {
            "speed": current["wind_speed_10m"],
            "gust": current["wind_gusts_10m"],
            "direction": current["wind_direction_10m"],
            "unit": "km/h"
        },

        "precipitation": {
            "last_1h_mm": round(rain_1h, 2),
            "last_3h_mm": round(rain_3h, 2),
            "last_6h_mm": round(rain_6h, 2),
            "last_24h_mm": round(rain_24h, 2)
        },

        "cloud_cover": {
            "value": current["cloud_cover"],
            "unit": "%"
        },

        "visibility": {
            "value": current["visibility"] / 1000,
            "unit": "km"
        },

        "uv_index": current["uv_index"],

        "dew_point": {
            "value": current["dew_point_2m"],
            "unit": "C"
        },

        "weather_condition_code":
            current["weather_code"],

        "weather_condition":
            weather_condition(
                current["weather_code"]
            )
    },

    "forecast": {
        "hourly": hourly_forecast,
        "daily": daily_forecast
    },

    "model_forecasts": {
        "GFS": gfs_forecast
    },

    "warnings": [
        imd_warning
    ],

    "air_quality": air_quality_values,

    "source_values": {

        "Open-Meteo": {
            "temperature_c":
                current["temperature_2m"],
            "humidity_pct":
                current["relative_humidity_2m"],
            "pressure_hpa":
                current["pressure_msl"],
            "wind_speed_kmh":
                current["wind_speed_10m"],
            "precipitation_mm":
                current["precipitation"]
        },

        "GFS": {
            "temperature_max_c":
                gfs_forecast["temperature_max_c"],
            "rainfall_24h_mm":
                gfs_forecast["rainfall_24h_mm"],
            "wind_max_kmh":
                gfs_forecast["wind_max_kmh"]
        },

        "WeatherAPI": weatherapi_values,

        "AirQuality": {
            "aqi":
                air_quality_current["european_aqi"],
            "pm25_ug_m3":
                air_quality_current["pm2_5"],
            "pm10_ug_m3":
                air_quality_current["pm10"],
            "no2_ug_m3":
                air_quality_current["nitrogen_dioxide"],
            "o3_ug_m3":
                air_quality_current["ozone"]
        }
    },

    "data_quality": {

        "missing_parameters": [],

        "source_reliability": {
            "Open-Meteo": "unknown",
            "GFS": "unknown",
            "WeatherAPI": "unknown",
            "IMD": "unknown",
            "AirQuality": "unknown"
        },

        "observation_age_seconds":
            observation_age_seconds,

        "processing_latency_seconds":
            latency_seconds,

        "gfs_latency_seconds":
            gfs_latency,

        "weatherapi_latency_seconds":
            weatherapi_latency,

        "air_quality_latency_seconds":
            air_quality_latency,

        "warning_timestamps_missing": True
    }
}


# ============================================================
# PRINT STANDARDIZED JSON
# ============================================================

print(
    json.dumps(
        standardized_data,
        indent=4
    )
)


# ============================================================
# SAVE STANDARDIZED JSON
# ============================================================

with open(
    "weather_standardized.json",
    "w"
) as file:

    json.dump(
        standardized_data,
        file,
        indent=4
    )

print("Standardized weather data saved.")