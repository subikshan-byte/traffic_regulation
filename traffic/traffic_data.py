import googlemaps
from datetime import datetime

# Replace with your Google API Key
API_KEY = "YOUR_API_KEY"

# Initialize Google Maps client
gmaps = googlemaps.Client(key=API_KEY)

def get_traffic_level(origin_lat, origin_lng, dest_lat, dest_lng):
    """
    Fetches real-time traffic data between two coordinates using Google Maps Directions API.
    Returns a simplified traffic level: Low, Moderate, High, or Critical.
    """

    origin = f"{origin_lat},{origin_lng}"
    destination = f"{dest_lat},{dest_lng}"
    now = datetime.now()

    directions_result = gmaps.directions(
        origin,
        destination,
        mode="driving",
        departure_time=now,
        traffic_model="best_guess"
    )

    # Extract required data
    route = directions_result[0]['legs'][0]
    normal_duration = route['duration']['value'] / 60          # in minutes
    traffic_duration = route['duration_in_traffic']['value'] / 60  # in minutes

    # Calculate delay ratio
    delay_ratio = traffic_duration / normal_duration

    # Classify traffic level
    if delay_ratio <= 1.1:
        traffic_level = "Low"
    elif 1.1 < delay_ratio <= 1.4:
        traffic_level = "Moderate"
    elif 1.4 < delay_ratio <= 1.8:
        traffic_level = "High"
    else:
        traffic_level = "Critical"

    return {
        "from": route['start_address'],
        "to": route['end_address'],
        "distance_km": route['distance']['text'],
        "normal_duration_min": round(normal_duration, 2),
        "traffic_duration_min": round(traffic_duration, 2),
        "traffic_level": traffic_level
    }