import requests
import json

url = "https://api.open-meteo.com/v1/gfs"

params = {
    "latitude": 20.2961,
    "longitude": 85.8245,
    "hourly": "temperature_2m,precipitation,wind_speed_10m",
    "daily": "temperature_2m_max,precipitation_sum,wind_speed_10m_max",
    "timezone": "Asia/Kolkata"
}

response = requests.get(url, params=params)

print("Status:", response.status_code)

data = response.json()

print(json.dumps(data, indent=4))