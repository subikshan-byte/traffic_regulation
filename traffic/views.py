from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Intersection, Road, PhoneSignal
from .floyd_warshall import FloydWarshallTraffic
import json
from datetime import timedelta
from django.utils import timezone

def index(request):
    return render(request, 'map.html')

def get_map_data(request):
    intersections = Intersection.objects.all()
    roads = Road.objects.all()
    
    intersections_data = [{
        'id': i.id,
        'name': i.name,
        'lat': i.latitude,
        'lng': i.longitude,
        'capacity': i.capacity
    } for i in intersections]
    
    roads_data = [{
        'id': r.id,
        'from': r.from_intersection.id,
        'to': r.to_intersection.id,
        'from_coords': {'lat': r.from_intersection.latitude, 'lng': r.from_intersection.longitude},
        'to_coords': {'lat': r.to_intersection.latitude, 'lng': r.to_intersection.longitude},
        'traffic_level': r.traffic_level,
        'current_traffic': r.current_traffic,
        'capacity': r.capacity,
        'travel_time': round(r.travel_time, 2)
    } for r in roads]
    
    return JsonResponse({
        'intersections': intersections_data,
        'roads': roads_data
    })

@csrf_exempt
@require_http_methods(["POST"])
def update_phone_signals(request):
    try:
        data = json.loads(request.body)
        device_id = data.get('device_id')
        road_id = data.get('road_id')
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        road = Road.objects.get(id=road_id)
        
        PhoneSignal.objects.create(
            device_id=device_id,
            road=road,
            latitude=lat,
            longitude=lng
        )
        
        # Count unique devices in last 5 minutes
        five_min_ago = timezone.now() - timedelta(minutes=5)
        recent_signals = PhoneSignal.objects.filter(
            road=road,
            timestamp__gte=five_min_ago
        ).values('device_id').distinct().count()
        
        road.current_traffic = recent_signals
        road.update_traffic_level()
        
        return JsonResponse({'status': 'success', 'traffic_count': recent_signals})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def get_optimal_route(request):
    data = json.loads(request.body)
    source_name = data.get('source')
    destination_name = data.get('destination')

    intersections = Intersection.objects.all()
    intersection_index = {inter.name: i for i, inter in enumerate(intersections)}
    index_intersection = {i: inter for inter, i in intersection_index.items()}

    n = len(intersections)
    INF = float('inf')
    dist = [[INF] * n for _ in range(n)]
    next_node = [[-1] * n for _ in range(n)]

    # Base: direct road distances
    for road in Road.objects.all():
        i, j = intersection_index[road.from_intersection.name], intersection_index[road.to_intersection.name]
        dist[i][j] = road.travel_time
        next_node[i][j] = j

    # Floyd–Warshall to compute all pairs shortest paths
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]

    def get_path(u, v):
        if next_node[u][v] == -1:
            return []
        path = [u]
        while u != v:
            u = next_node[u][v]
            path.append(u)
        return path

    src, dst = intersection_index[source_name], intersection_index[destination_name]
    optimal_path = get_path(src, dst)
    optimal_distance = dist[src][dst]

    # Get main route roads
    main_roads = []
    for i in range(len(optimal_path) - 1):
        from_node = index_intersection[optimal_path[i]]
        to_node = index_intersection[optimal_path[i + 1]]
        road = Road.objects.get(from_intersection=from_node, to_intersection=to_node)
        main_roads.append({
            "from": from_node.name,
            "to": to_node.name,
            "traffic": road.traffic_level,
            "travel_time": road.travel_time,
        })

    # 🔄 Alternate route: avoid most congested road from main route
    congested = sorted(main_roads, key=lambda x: ['low','medium','high','critical'].index(x['traffic']), reverse=True)[0]
    avoid_road = Road.objects.get(from_intersection__name=congested["from"], to_intersection__name=congested["to"])

    # Temporarily set high cost for congested road
    backup_cost = dist[intersection_index[avoid_road.from_intersection.name]][intersection_index[avoid_road.to_intersection.name]]
    dist[intersection_index[avoid_road.from_intersection.name]][intersection_index[avoid_road.to_intersection.name]] = INF

    # Re-run Floyd–Warshall for alternate route
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]

    alternate_path = get_path(src, dst)
    alternate_roads = []
    for i in range(len(alternate_path) - 1):
        from_node = index_intersection[alternate_path[i]]
        to_node = index_intersection[alternate_path[i + 1]]
        road = Road.objects.get(from_intersection=from_node, to_intersection=to_node)
        alternate_roads.append({
            "from": from_node.name,
            "to": to_node.name,
            "traffic": road.traffic_level,
            "travel_time": road.travel_time,
        })

    # Restore original cost
    dist[intersection_index[avoid_road.from_intersection.name]][intersection_index[avoid_road.to_intersection.name]] = backup_cost

    return JsonResponse({
        "main_route": main_roads,
        "alternate_route": alternate_roads,
    })

from django.http import JsonResponse
import random

def simulate_traffic(request):
    """Simulate traffic updates and return road data"""
    roads = Road.objects.all()
    road_list = []

    for road in roads:
        # Simulate random traffic
        road.current_traffic = random.randint(0, road.capacity)
        road.update_traffic_level()
        road.save()

        # Collect data for frontend
        road_list.append({
            'from': getattr(road.start, 'name', 'Unknown'),
            'to': getattr(road.end, 'name', 'Unknown'),
            'traffic': getattr(road, 'traffic_level', 'low'),
            'travel_time': getattr(road, 'travel_time', 5),
        })

    return JsonResponse({'roads': road_list})

from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import math

def haversine_km(lat1, lon1, lat2, lon2):
    # returns distance in kilometers
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_route_traffic(request):
    start_id = request.GET.get('start')
    end_id = request.GET.get('end')

    if not start_id or not end_id:
        return JsonResponse({'error': 'Start and end points required'}, status=400)

    # Find route via Floyd-Warshall (you already have this)
    fw = FloydWarshallTraffic()
    route_data = fw.find_optimal_route(int(start_id), int(end_id))

    # Time window used to count signals (example uses last 24 hours — adjust as needed)
    one_day_ago = timezone.now() - timedelta(hours=24)
    segments = []
    total_time_min = 0.0

    # Traffic speed multipliers (applied to base speed)
    # Higher traffic -> lower multiplier -> lower effective speed -> higher time
    traffic_speed_multiplier = {
        'low': 1.0,
        'medium': 0.75,
        'high': 0.5,
        'critical': 0.35
    }

    for seg in route_data['segments']:
        # get the road object
        road = Road.objects.get(from_intersection__name=seg['from'], to_intersection__name=seg['to'])

        # count unique devices in window
        recent_signals = PhoneSignal.objects.filter(
            road=road,
            timestamp__gte=one_day_ago
        ).values('device_id').distinct().count()

        road.current_traffic = recent_signals
        road.update_traffic_level()
        # optional: save updated traffic if you want persistence
        # road.save()

        # --- DISTANCE: prefer stored road.distance (assumed meters), else compute by coordinates
        distance_km = None
        if hasattr(road, 'distance') and road.distance is not None:
            try:
                # if distance stored in meters:
                distance_km = float(road.distance) / 1000.0
            except Exception:
                distance_km = None

        if distance_km is None:
            # fallback: compute via haversine using intersection coords
            from_lat = road.from_intersection.latitude
            from_lng = road.from_intersection.longitude
            to_lat = road.to_intersection.latitude
            to_lng = road.to_intersection.longitude
            distance_km = haversine_km(from_lat, from_lng, to_lat, to_lng)

        # --- BASE SPEED: prefer road.speed_limit if present, else fallback default (city roads)
        base_speed_kmph = 40.0  # reasonable city average; adjust to your region
        if hasattr(road, 'speed_limit') and road.speed_limit:
            try:
                base_speed_kmph = float(road.speed_limit)
            except Exception:
                pass

        # --- TRAFFIC MULTIPLIER
        level = getattr(road, 'traffic_level', 'low')
        multiplier = traffic_speed_multiplier.get(level, 1.0)

        # Effective speed (apply multiplier). Enforce a minimum speed floor (km/h)
        effective_speed_kmph = base_speed_kmph * multiplier
        MIN_SPEED_KMPH = 5.0  # don't allow speed below this to avoid extreme times
        if effective_speed_kmph < MIN_SPEED_KMPH:
            effective_speed_kmph = MIN_SPEED_KMPH

        # Calculated travel time in minutes from distance and effective speed
        # time (hours) = distance_km / speed_kmph => minutes = *60
        calc_travel_time_min = 0.0
        if distance_km > 0 and effective_speed_kmph > 0:
            calc_travel_time_min = (distance_km / effective_speed_kmph) * 60.0

        # If the model already stores a measured travel_time (in minutes or hours), try to use it:
        # Common patterns: road.travel_time might already be in minutes. If in hours or other unit, adjust accordingly.
        db_travel_time_min = None
        if hasattr(road, 'travel_time') and road.travel_time is not None:
            try:
                db_travel_time_min = float(road.travel_time)  # assume it's already minutes
            except Exception:
                db_travel_time_min = None

        # Merge strategy:
        # - If DB travel_time exists and is reasonable, blend both values (weighted average).
        # - Otherwise use calculated value.
        travel_time_min = calc_travel_time_min
        if db_travel_time_min and db_travel_time_min > 0:
            # If values differ massively, you might prefer the measured one. We'll average.
            travel_time_min = round((calc_travel_time_min + db_travel_time_min) / 2.0, 2)
        else:
            travel_time_min = round(calc_travel_time_min, 2)

        # add to summaries
        total_time_min += travel_time_min

        segments.append({
            'from': road.from_intersection.name,
            'to': road.to_intersection.name,
            'traffic_level': road.traffic_level,
            'current_traffic': road.current_traffic,
            'capacity': road.capacity,
            'distance_km': round(distance_km, 3),
            'travel_time_min': travel_time_min,
            'from_coords': {'lat': road.from_intersection.latitude, 'lng': road.from_intersection.longitude},
            'to_coords': {'lat': road.to_intersection.latitude, 'lng': road.to_intersection.longitude},
        })

    # Prepare time window for the route stats: End = now, Start = End - total_time
    end_time = timezone.now()
    start_time = end_time - timedelta(minutes=total_time_min)

    time_window = {
        'start': start_time.isoformat(),
        'end': end_time.isoformat(),
        'total_time_min': round(total_time_min, 2)
    }

    return JsonResponse({
        'status': 'success',
        'route': route_data,
        'segments': segments,
        'time_window': time_window
    })
