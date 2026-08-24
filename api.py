from fastapi import FastAPI, Query
import requests
import json
import os
import time
from datetime import datetime


app = FastAPI(
    title="Weather Standardized API",
    version="1.0"
)


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


def get_location_metadata(lat: float, lon: float):
    url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "addressdetails": 1,
        "accept-language": "en"
    }

    headers = {
        "User-Agent": "WeatherGPT-Data-API/1.0"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception("Geocoding request failed")

        data = response.json()
        address = data.get("address", {})

        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
        )

        district = (
            address.get("state_district")
            or address.get("county")
        )

        return {
            "latitude": lat,
            "longitude": lon,
            "city": city,
            "district": district,
            "state": address.get("state"),
            "country": address.get("country")
        }

    except Exception:
        return {
            "latitude": lat,
            "longitude": lon,
            "city": None,
            "district": None,
            "state": None,
            "country": None
        }


@app.get("/")
def home():
    return {
        "message": "Weather API is running"
    }


@app.get("/api/v1/location")
def location(
    lat: float = Query(...),
    lon: float = Query(...)
):
    return get_location_metadata(lat, lon)


@app.get("/api/v1/weather/current")
def current_weather(
    lat: float = Query(...),
    lon: float = Query(...)
):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "pressure_msl,"
            "wind_speed_10m,"
            "wind_gusts_10m,"
            "wind_direction_10m,"
            "precipitation,"
            "cloud_cover,"
            "visibility,"
            "uv_index,"
            "dew_point_2m,"
            "weather_code"
        ),
        "timezone": "auto"
    }

    start = time.time()

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    latency = round(time.time() - start, 3)

    if response.status_code != 200:
        return {
            "error": "Weather provider request failed",
            "status_code": response.status_code,
            "latency_seconds": latency
        }

    data = response.json()
    current = data["current"]

    location_data = get_location_metadata(lat, lon)
    location_data["timezone"] = data["timezone"]
    location_data["elevation_m"] = data["elevation"]

    retrieved_at = datetime.now().astimezone().isoformat()

    return {
        "location": location_data,

        "metadata": {
            "generated_at": current["time"],
            "source": "Open-Meteo",
            "source_type": "observation",
            "retrieved_at": retrieved_at,
            "request_latency_seconds": latency
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
                "last_1h_mm": current["precipitation"]
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
            "weather_code": current["weather_code"],
            "weather_condition": weather_condition(
                current["weather_code"]
            )
        },

        "data_quality": {
            "missing_parameters": [],
            "request_latency_seconds": latency
        }
    }


@app.get("/api/v1/weather/forecast")
def weather_forecast(
    lat: float = Query(...),
    lon: float = Query(...)
):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "precipitation_probability,"
            "wind_speed_10m,"
            "wind_gusts_10m,"
            "wind_direction_10m,"
            "cloud_cover,"
            "visibility,"
            "dew_point_2m,"
            "weather_code"
        ),
        "daily": (
            "temperature_2m_min,"
            "temperature_2m_max,"
            "precipitation_sum,"
            "precipitation_probability_max,"
            "wind_speed_10m_max,"
            "wind_gusts_10m_max,"
            "wind_direction_10m_dominant,"
            "uv_index_max,"
            "weather_code"
        ),
        "timezone": "auto"
    }

    start = time.time()

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    latency = round(time.time() - start, 3)

    if response.status_code != 200:
        return {
            "error": "Forecast provider request failed",
            "status_code": response.status_code,
            "latency_seconds": latency
        }

    data = response.json()
    hourly = data["hourly"]
    daily = data["daily"]

    location_data = get_location_metadata(lat, lon)
    location_data["timezone"] = data["timezone"]
    location_data["elevation_m"] = data["elevation"]

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

    return {
        "location": location_data,

        "metadata": {
            "source": "Open-Meteo",
            "source_type": "forecast",
            "retrieved_at":
                datetime.now().astimezone().isoformat(),
            "request_latency_seconds": latency
        },

        "forecast": {
            "hourly": hourly_forecast,
            "daily": daily_forecast
        },

        "data_quality": {
            "missing_parameters": [],
            "request_latency_seconds": latency
        }
    }


@app.get("/api/v1/weather/nwp")
def weather_nwp(
    lat: float = Query(...),
    lon: float = Query(...)
):

    url = "https://api.open-meteo.com/v1/gfs"

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": (
            "temperature_2m_max,"
            "precipitation_sum,"
            "wind_speed_10m_max"
        ),
        "timezone": "auto"
    }

    start = time.time()

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    latency = round(time.time() - start, 3)

    if response.status_code != 200:
        return {
            "error": "GFS request failed",
            "status_code": response.status_code,
            "latency_seconds": latency
        }

    data = response.json()
    daily = data["daily"]

    location_data = get_location_metadata(lat, lon)
    location_data["timezone"] = data["timezone"]
    location_data["elevation_m"] = data["elevation"]

    return {
        "location": location_data,

        "metadata": {
            "source": "GFS via Open-Meteo",
            "source_type": "NWP",
            "retrieved_at":
                datetime.now().astimezone().isoformat(),
            "request_latency_seconds": latency
        },

        "model_forecasts": {
            "GFS": {
                "model_forecast_time": daily["time"][0],
                "temperature_max_c":
                    daily["temperature_2m_max"][0],
                "rainfall_24h_mm":
                    daily["precipitation_sum"][0],
                "wind_max_kmh":
                    daily["wind_speed_10m_max"][0]
            }
        },

        "data_quality": {
            "missing_parameters": [],
            "request_latency_seconds": latency
        }
    }


@app.get("/api/v1/weather/warnings")
def weather_warnings(
    lat: float = Query(...),
    lon: float = Query(...)
):

    location_data = get_location_metadata(lat, lon)
    district = location_data.get("district")

    if not district:
        return {
            "location": location_data,
            "metadata": {
                "source": "IMD",
                "source_type": "official_warning"
            },
            "warnings": [],
            "data_quality": {
                "warning_data_available": False,
                "reason": "District could not be identified"
            }
        }

    # Currently automated IMD warning data is available
    # only for the Khordha data source we collected.
    if district.lower() != "khordha":
        return {
            "location": location_data,
            "metadata": {
                "source": "IMD",
                "source_type": "official_warning"
            },
            "warnings": [],
            "data_quality": {
                "warning_data_available": False,
                "reason": (
                    "Automated IMD warning source is "
                    "not configured for this district yet"
                )
            }
        }

    try:
        with open("imd_warning.json", "r") as file:
            warning = json.load(file)

    except FileNotFoundError:
        return {
            "location": location_data,
            "metadata": {
                "source": "IMD",
                "source_type": "official_warning"
            },
            "warnings": [],
            "data_quality": {
                "warning_data_available": False,
                "reason": "imd_warning.json not found"
            }
        }

    return {
        "location": location_data,
        "metadata": {
            "source": "IMD",
            "source_type": "official_warning"
        },
        "warnings": [
            warning
        ],
        "data_quality": {
            "warning_data_available": True,
            "warning_timestamps_missing": True
        }
    }
    try:
        with open("imd_warning.json", "r") as file:
            warning = json.load(file)
    except FileNotFoundError:
        return {
            "error": "imd_warning.json not found"
        }

    location_data = get_location_metadata(lat, lon)

    return {
        "location": location_data,

        "metadata": {
            "source": "IMD",
            "source_type": "official_warning"
        },

        "warnings": [
            warning
        ],

        "data_quality": {
            "warning_timestamps_missing": True
        }
    }


@app.get("/api/v1/weather/air-quality")
def air_quality(
    lat: float = Query(...),
    lon: float = Query(...)
):

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "european_aqi,"
            "pm2_5,"
            "pm10,"
            "nitrogen_dioxide,"
            "ozone"
        ),
        "timezone": "auto"
    }

    start = time.time()

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    latency = round(time.time() - start, 3)

    if response.status_code != 200:
        return {
            "error": "Air quality provider request failed",
            "status_code": response.status_code,
            "latency_seconds": latency
        }

    data = response.json()
    current = data["current"]

    location_data = get_location_metadata(lat, lon)
    location_data["timezone"] = data["timezone"]
    location_data["elevation_m"] = data.get("elevation")

    return {
        "location": location_data,

        "metadata": {
            "source": "Open-Meteo Air Quality",
            "source_type": "air_quality",
            "retrieved_at":
                datetime.now().astimezone().isoformat(),
            "request_latency_seconds": latency
        },

        "air_quality": {
            "aqi": current["european_aqi"],
            "aqi_standard": "European AQI",
            "pm25_ug_m3": current["pm2_5"],
            "pm10_ug_m3": current["pm10"],
            "no2_ug_m3": current["nitrogen_dioxide"],
            "o3_ug_m3": current["ozone"]
        },

        "data_quality": {
            "missing_parameters": [],
            "request_latency_seconds": latency
        }
    }


def get_weatherapi_current(lat: float, lon: float):

    api_key = os.getenv("WEATHER_API_KEY")

    if not api_key:
        return {
            "error": "WEATHER_API_KEY is not set"
        }

    url = "https://api.weatherapi.com/v1/current.json"

    params = {
        "key": api_key,
        "q": f"{lat},{lon}"
    }

    start = time.time()

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    latency = round(time.time() - start, 3)

    if response.status_code != 200:
        return {
            "error": "WeatherAPI request failed",
            "status_code": response.status_code,
            "latency_seconds": latency
        }

    data = response.json()
    current = data["current"]

    return {
        "values": {
            "temperature_c": current["temp_c"],
            "humidity_pct": current["humidity"],
            "pressure_hpa": current["pressure_mb"],
            "wind_speed_kmh": current["wind_kph"],
            "wind_direction_deg": current["wind_degree"],
            "precipitation_mm": current["precip_mm"],
            "cloud_cover_pct": current["cloud"],
            "feels_like_c": current["feelslike_c"],
            "visibility_km": current["vis_km"],
            "uv_index": current["uv"]
        },
        "latency_seconds": latency,
        "observed_at": current["last_updated"],
        "source": "WeatherAPI"
    }


@app.get("/api/v1/weather/complete")
def complete_weather(
    lat: float = Query(...),
    lon: float = Query(...)
):

    current = current_weather(lat, lon)
    forecast = weather_forecast(lat, lon)
    nwp = weather_nwp(lat, lon)
    warnings = weather_warnings(lat, lon)
    air_quality_data = air_quality(lat, lon)
    weatherapi = get_weatherapi_current(lat, lon)

    if "error" in current:
        return current

    if "error" in forecast:
        return forecast

    if "error" in nwp:
        return nwp

    if "error" in air_quality_data:
        return air_quality_data

    location_data = current["location"]

    return {
        "location": location_data,

        "metadata": {
            "generated_at":
                current["metadata"]["generated_at"],
            "source": "Multiple sources",
            "source_type": "combined",
            "retrieved_at":
                current["metadata"]["retrieved_at"]
        },

        "current_weather":
            current["current_weather"],

        "forecast":
            forecast["forecast"],

        "model_forecasts":
            nwp["model_forecasts"],

        "warnings":
            warnings["warnings"],

        "air_quality":
            air_quality_data["air_quality"],

        "sources": {
            "current_weather": "Open-Meteo",
            "forecast": "Open-Meteo",
            "nwp": "GFS via Open-Meteo",
            "warnings": "IMD",
            "air_quality": "Open-Meteo Air Quality",
            "comparison_source": "WeatherAPI"
        },

        "source_values": {
            "Open-Meteo": {
                "temperature_c":
                    current["current_weather"]
                    ["temperature"]["value"],
                "humidity_pct":
                    current["current_weather"]
                    ["humidity"]["value"],
                "pressure_hpa":
                    current["current_weather"]
                    ["pressure"]["value"],
                "wind_speed_kmh":
                    current["current_weather"]
                    ["wind"]["speed"]
            },

            "WeatherAPI":
                weatherapi.get("values", {}),

            "GFS":
                nwp["model_forecasts"]["GFS"],

            "AirQuality":
                air_quality_data["air_quality"]
        },

        "data_quality": {
            "missing_parameters": [],

            "source_reliability": {
                "Open-Meteo": "unknown",
                "WeatherAPI": "unknown",
                "GFS": "unknown",
                "IMD": "unknown",
                "AirQuality": "unknown"
            },

            "source_latency_seconds": {
                "Open-Meteo":
                    current["metadata"]
                    ["request_latency_seconds"],

                "WeatherAPI":
                    weatherapi.get(
                        "latency_seconds"
                    ),

                "GFS":
                    nwp["metadata"]
                    ["request_latency_seconds"],

                "AirQuality":
                    air_quality_data["metadata"]
                    ["request_latency_seconds"]
            },

            "warning_timestamps_missing": True
        }
    }