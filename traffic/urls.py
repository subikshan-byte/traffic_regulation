# traffic_regulation/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/map-data/', views.get_map_data, name='map_data'),
    path('api/update-signals/', views.update_phone_signals, name='update_signals'),
    path('api/optimal-route/', views.get_optimal_route, name='optimal_route'),
    path('api/simulate-traffic/', views.simulate_traffic, name='simulate_traffic'),
path('api/route-traffic/', views.get_route_traffic, name='route_traffic'),
path('update-google-traffic/', views.update_traffic_from_google, name='update_google_traffic'),

]
