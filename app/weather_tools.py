import urllib.request
import json
from typing import Dict, Any

# Toronto Zoo Coordinates: 43.8200° N, 79.1815° W
ZOO_LAT = 43.8200
ZOO_LNG = -79.1815

WEATHER_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    95: "Thunderstorm",
}


def get_zoo_weather_and_visibility_impact() -> Dict[str, Any]:
    """Fetch live weather conditions at the Toronto Zoo to assess outdoor animal visibility.

    Returns:
        Live temperature, weather conditions, precipitation, and its expected impact on animal visibility.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={ZOO_LAT}&longitude={ZOO_LNG}&"
        f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&"
        f"timezone=America%2FToronto"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "ZooNow-Agent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        return {"error": f"Failed to fetch live weather: {str(e)}"}

    current = data.get("current", {})
    temp_c = current.get("temperature_2m")
    apparent_temp_c = current.get("apparent_temperature")
    precip = current.get("precipitation", 0.0)
    wcode = current.get("weather_code", 0)
    wind_kmh = current.get("wind_speed_10m", 0.0)
    condition = WEATHER_CODE_MAP.get(wcode, "Cloudy/Variable")

    # Assess animal behavior impact
    if precip > 1.0 or wcode in [61, 63, 65, 95]:
        visibility_hint = (
            "Rain detected: Outdoor savanna & trek animals (lions, giraffes) often seek indoor shelters or covered canopies. "
            "Indoor pavilions (African Rainforest, Australasia) are recommended!"
        )
    elif temp_c is not None and temp_c >= 25.0:
        visibility_hint = (
            "Warm afternoon: Animals like Amur Tigers, Arctic Foxes, and Lions tend to nap in shaded crevices or dens. "
            "Polar bears may be in the underwater pool."
        )
    elif temp_c is not None and temp_c <= 5.0:
        visibility_hint = (
            "Cool weather: Cold-tolerant animals (Polar Bears, Arctic Foxes, Amur Tigers) are usually very active outdoors!"
        )
    else:
        visibility_hint = "Mild conditions: Moderate animal activity across both outdoor trails and pavilions."

    return {
        "location": "Toronto Zoo (Scarborough, ON)",
        "temperature_celsius": temp_c,
        "feels_like_celsius": apparent_temp_c,
        "condition": condition,
        "precipitation_mm": precip,
        "wind_speed_kmh": wind_kmh,
        "animal_visibility_impact": visibility_hint,
    }
