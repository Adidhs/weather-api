import requests
import json

url = "https://sachet.ndma.gov.in/cap_public_website/FetchLocationWiseAlerts"

params = {
    "lat": 20.356371885275895,
    "long": 85.82052655956794,
    "radius": 20
}

try:
    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    print("STATUS CODE:", response.status_code)
    print("CONTENT TYPE:", response.headers.get("content-type"))
    print()

    print("RAW RESPONSE:")
    print(response.text)

    print()
    print("PARSED RESPONSE:")

    try:
        data = response.json()
        print(json.dumps(data, indent=2))
    except ValueError:
        print("Response is not JSON.")

except requests.RequestException as e:
    print("REQUEST FAILED:")
    print(e)    