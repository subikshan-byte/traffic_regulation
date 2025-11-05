from celery import shared_task
import requests
from .models import Road

@shared_task
def update_traffic_data():
    api_key = "YOUR_GOOGLE_MAPS_API_KEY"
    for road in Road.objects.all():
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={road.start_point}&destinations={road.end_point}&departure_time=now&traffic_model=best_guess&key={api_key}"
        response = requests.get(url).json()

        if response['status'] == 'OK':
            element = response['rows'][0]['elements'][0]
            road.current_time = element['duration_in_traffic']['value']
            road.save()
