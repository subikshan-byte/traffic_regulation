from .models import Intersection, Road
import sys

class FloydWarshallTraffic:
    def __init__(self):
        self.intersections = list(Intersection.objects.all())
        self.roads = list(Road.objects.all())
        self.n = len(self.intersections)
        self.INF = sys.maxsize
        
        # Create mappings
        self.id_to_index = {i.id: idx for idx, i in enumerate(self.intersections)}
        self.index_to_id = {idx: i.id for idx, i in enumerate(self.intersections)}
        
        # Initialize matrices
        self.dist = [[self.INF] * self.n for _ in range(self.n)]
        self.next_node = [[None] * self.n for _ in range(self.n)]
        
        # Set distances
        for i in range(self.n):
            self.dist[i][i] = 0
            self.next_node[i][i] = i
        
        for road in self.roads:
            from_idx = self.id_to_index[road.from_intersection.id]
            to_idx = self.id_to_index[road.to_intersection.id]
            weight = road.travel_time
            
            self.dist[from_idx][to_idx] = weight
            self.next_node[from_idx][to_idx] = to_idx
    
    def compute(self):
        # Floyd-Warshall algorithm
        for k in range(self.n):
            for i in range(self.n):
                for j in range(self.n):
                    if self.dist[i][k] != self.INF and self.dist[k][j] != self.INF:
                        if self.dist[i][k] + self.dist[k][j] < self.dist[i][j]:
                            self.dist[i][j] = self.dist[i][k] + self.dist[k][j]
                            self.next_node[i][j] = self.next_node[i][k]
    
    def get_path(self, start_idx, end_idx):
        if self.next_node[start_idx][end_idx] is None:
            return []
        
        path = [start_idx]
        while start_idx != end_idx:
            start_idx = self.next_node[start_idx][end_idx]
            path.append(start_idx)
        
        return path
    
    def find_optimal_route(self, start_id, end_id):
        self.compute()
        
        start_idx = self.id_to_index.get(start_id)
        end_idx = self.id_to_index.get(end_id)
        
        if start_idx is None or end_idx is None:
            return {'error': 'Invalid intersection IDs'}
        
        path_indices = self.get_path(start_idx, end_idx)
        
        if not path_indices:
            return {'error': 'No path found'}
        
        path_ids = [self.index_to_id[idx] for idx in path_indices]
        path_intersections = [Intersection.objects.get(id=pid) for pid in path_ids]
        
        total_time = self.dist[start_idx][end_idx]
        
        route_segments = []
        for i in range(len(path_ids) - 1):
            road = Road.objects.filter(
                from_intersection_id=path_ids[i],
                to_intersection_id=path_ids[i + 1]
            ).first()
            
            if road:
                route_segments.append({
                    'from': road.from_intersection.name,
                    'to': road.to_intersection.name,
                    'from_coords': {
                        'lat': road.from_intersection.latitude,
                        'lng': road.from_intersection.longitude
                    },
                    'to_coords': {
                        'lat': road.to_intersection.latitude,
                        'lng': road.to_intersection.longitude
                    },
                    'traffic_level': road.traffic_level,
                    'travel_time': round(road.travel_time, 2)
                })
        
        return {
            'path': [{'id': i.id, 'name': i.name, 'lat': i.latitude, 'lng': i.longitude} 
                     for i in path_intersections],
            'total_time': round(total_time, 2),
            'segments': route_segments
        }