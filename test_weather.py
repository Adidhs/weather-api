import requests
import json
import time
from datetime import datetime

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 20.2961,
    "longitude": 85.8245,
   "current": "temperature_2m,relative_humidity_2m,apparent_temperature,pressure_msl,wind_speed_10m,wind_gusts_10m,wind_direction_10m,precipitation,cloud_cover,visibility,uv_index,dew_point_2m,weather_code",
   "hourly": "temperature_2m,relative_humidity_2m,precipitation,precipitation_probability,wind_speed_10m,wind_gusts_10m,wind_direction_10m,cloud_cover,visibility,weather_code,dew_point_2m",
    "daily": "temperature_2m_min,temperature_2m_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,weather_code,uv_index_max",
    "timezone": "Asia/Kolkata"
}

# Start measuring API request time
request_start = time.time()

response = requests.get(
    url,
    params=params,
    timeout=30
)

# Stop measuring API request time
request_end = time.time()

request_latency = round(
    request_end - request_start,
    3
)

print("Status:", response.status_code)

# Convert response to JSON
data = response.json()

# Record when we received the data
retrieved_at = datetime.now().astimezone().isoformat()

# Add collection information
data["collection_metadata"] = {
    "source": "Open-Meteo",
    "retrieved_at": retrieved_at,
    "request_latency_seconds": request_latency
}

# Save raw data
with open("weather_raw.json", "w") as file:
    json.dump(data, file, indent=4)

print("Weather data saved to weather_raw.json")