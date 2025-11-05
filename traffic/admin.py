from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Intersection, Road

@admin.register(Intersection)
class IntersectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude', 'capacity']

@admin.register(Road)
class RoadAdmin(admin.ModelAdmin):
    list_display = ['from_intersection', 'to_intersection', 'distance', 
                    'current_traffic', 'capacity', 'traffic_level', 'travel_time']
    list_filter = ['traffic_level']

