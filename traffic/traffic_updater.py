# traffic_updater.py
import requests
from django.conf import settings
from django.utils import timezone
from .models import RouteTraffic

def fetch_live_traffic(start, end):
    """Fetch traffic between two places using Google Distance Matrix."""
    url = (
        f"https://maps.googleapis.com/maps/api/distancematrix/json?"
        f"origins={start}&destinations={end}&departure_time=now&key={settings.GOOGLE_MAPS_API_KEY}"
    )
    r = requests.get(url)
    data = r.json()

    if data["status"] != "OK":
        print("Traffic API error:", data)
        return None

    elem = data["rows"][0]["elements"][0]
    distance_km = elem["distance"]["value"] / 1000
    normal_time = elem["duration"]["value"] / 60
    traffic_time = elem["duration_in_traffic"]["value"] / 60

    delay_ratio = traffic_time / normal_time

    if delay_ratio < 1.2:
        level = "LOW"
    elif delay_ratio < 1.5:
        level = "MEDIUM"
    elif delay_ratio < 2.0:
        level = "HIGH"
    else:
        level = "CRITICAL"

    route, _ = RouteTraffic.objects.get_or_create(start=start, end=end)
    route.distance_km = distance_km
    route.normal_time_min = normal_time
    route.traffic_time_min = traffic_time
    route.congestion_level = level
    route.last_updated = timezone.now()
    route.save()

    return route
