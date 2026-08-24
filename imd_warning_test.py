import requests
import json

# IMD district warning API
url = "https://mausam.imd.gov.in/api/warnings_district_api.php"

# IMPORTANT:
# We are using 573 only as the example object ID from IMD's documentation.
# We still need to confirm the correct ID for Khordha.
params = {
    "id": 573
}

response = requests.get(
    url,
    params=params,
    timeout=30
)

print("Status:", response.status_code)
print("URL:", response.url)

print("Response:")
print(response.text)