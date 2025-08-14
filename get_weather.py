# app.py
import os
import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Read Google API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment")
GOOGLE_API_KEY = GOOGLE_API_KEY.strip()

app = FastAPI(title="Outdoorec Weather Service")


def geocode_location(location_str: str):
    """Convert ZIP code, city, or landmark into latitude and longitude."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location_str}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") != "OK" or not data.get("results"):
        raise HTTPException(status_code=400, detail=f"Could not geocode location: {location_str}")

    location = data["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]


def c_to_f(celsius):
    return celsius * 9 / 5 + 32


def get_weather(lat, lon):
    """Fetch current weather from Google Weather API."""
    url = f"https://weather.googleapis.com/v1/currentConditions:lookup?key={GOOGLE_API_KEY}&location.latitude={lat}&location.longitude={lon}"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error retrieving weather data: {response.text}")
    data = response.json()

    weather = data.get("weatherCondition", {})
    temp_c = data.get("temperature", {}).get("degrees")
    feels_c = data.get("feelsLikeTemperature", {}).get("degrees")
    humidity = data.get("relativeHumidity")
    wind = data.get("wind", {})
    wind_speed_kph = wind.get("speed", {}).get("value")
    wind_direction = wind.get("direction", {}).get("cardinal")
    description = weather.get("description", {}).get("text", "Unknown")

    forecast = {
        "location": {"lat": lat, "lon": lon},
        "condition": description,
        "temperature_F": round(c_to_f(temp_c), 1) if temp_c is not None else None,
        "feels_like_F": round(c_to_f(feels_c), 1) if feels_c is not None else None,
        "humidity": humidity,
        "wind": {"speed_kph": wind_speed_kph, "direction": wind_direction},
    }
    return forecast


@app.get("/weather")
def weather(location: str = Query(..., description="ZIP code, city, or landmark")):
    lat, lon = geocode_location(location)
    return get_weather(lat, lon)


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("get_weather:app", host="0.0.0.0", port=port, reload=True)
