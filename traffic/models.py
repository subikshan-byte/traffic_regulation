from django.db import models
from django.utils import timezone
import json

class Intersection(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    capacity = models.IntegerField(default=100)  
    
    def __str__(self):
        return self.name

class Road(models.Model):
    TRAFFIC_LEVELS = [
        ('low', 'Low - Green'),
        ('medium', 'Medium - Yellow'),
        ('high', 'High - Orange'),
        ('critical', 'Critical - Red'),
    ]
    
    from_intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='outgoing_roads')
    to_intersection = models.ForeignKey(Intersection, on_delete=models.CASCADE, related_name='incoming_roads')
    distance = models.FloatField()  
    capacity = models.IntegerField(default=50)  
    current_traffic = models.IntegerField(default=0)
    traffic_level = models.CharField(max_length=10, choices=TRAFFIC_LEVELS, default='low')
    travel_time = models.FloatField(default=0)  
    
    def update_traffic_level(self):
        ratio = self.current_traffic / self.capacity if self.capacity > 0 else 0
        if ratio >= 0.9:
            self.traffic_level = 'critical'
        elif ratio >= 0.7:
            self.traffic_level = 'high'
        elif ratio >= 0.4:
            self.traffic_level = 'medium'
        else:
            self.traffic_level = 'low'
        
        base_time = self.distance * 2 
        
        multiplier = 1 + (ratio * 2)  
        self.travel_time = base_time * multiplier
        self.save()
    
    def __str__(self):
        return f"{self.from_intersection.name} -> {self.to_intersection.name}"

class PhoneSignal(models.Model):
    device_id = models.CharField(max_length=100)
    road = models.ForeignKey(Road, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    class Meta:
        ordering = ['-timestamp']