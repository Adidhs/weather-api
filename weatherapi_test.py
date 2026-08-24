import requests
import os

API_KEY = os.getenv("WEATHER_API_KEY")

if not API_KEY:
    print("ERROR: WEATHER_API_KEY is not set.")
    exit()

url = "https://api.weatherapi.com/v1/current.json"

params = {
    "key": API_KEY,
    "q": "20.2961,85.8245"
}

response = requests.get(url, params=params)

print("Status:", response.status_code)
print("Response:", response.text)   