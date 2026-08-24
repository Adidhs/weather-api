import requests
import re
import json
# IMD public district warning page
url = "https://mausam.imd.gov.in/imd_latest/contents/districtwise-warning_mc.php?id=10"

response = requests.get(url, timeout=30)

print("Status:", response.status_code)

if response.status_code != 200:
    print("Failed to access IMD warning page")
    raise SystemExit()

page = response.text

# Find the Khordha district block
pattern = r'"title"\s*:\s*"KHORDHA".*?"id"\s*:\s*"174".*?"color"\s*:\s*"(.*?)".*?"balloonText"\s*:\s*"(.*?)"'

match = re.search(pattern, page, re.DOTALL)

if not match:
    print("Khordha warning data not found")
    raise SystemExit()

color = match.group(1)
balloon_text = match.group(2)


# Remove HTML tags from balloon text
clean_text = re.sub(r"<.*?>", " ", balloon_text)

# Remove escaped HTML characters
clean_text = clean_text.replace("\\/", "/")
clean_text = re.sub(r"\s+", " ", clean_text).strip()

# Convert IMD color to warning level
color_map = {
    "#008000": "green",
    "#FFFF00": "yellow",
    "#FFA500": "orange",
    "#FF0000": "red"
}

severity = color_map.get(color.upper(), "unknown")

warning_data = {
    "active": severity != "green",
    "severity": severity,
    "source_color": color,
    "severity_label": {
        "green": "no_warning",
        "yellow": "watch",
        "orange": "alert",
        "red": "warning"
    }.get(severity, "unknown"),
    "title": "IMD Weather Warning",
    "description": clean_text,
    "affected_area": "Khordha",
    "district_id": 174,
    "source": "IMD"
}

with open("imd_warning.json", "w") as file:
    json.dump(warning_data, file, indent=4)

print("IMD warning saved to imd_warning.json")

print("Khordha color:", color)
print("Khordha warning:", balloon_text)