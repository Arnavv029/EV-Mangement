"""
Emergency Views
================
Endpoints:
  GET /api/emergency/mechanics/  → Nearby mechanics sorted by distance
  GET /api/emergency/stations/   → All stations (reused for Battery & Charger emergencies)

These are read-only, authenticated endpoints used by the Emergency section
on the user's home page.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Mechanic, Station
from core.serializers import MechanicSerializer, StationSerializer
from core.utils.distance import haversine_distance, sort_stations_by_distance

from django.db.models import Avg, Count, Value, FloatField
from django.db.models.functions import Coalesce


# ─────────────────────────────────────────────────────────────────────────────
# NEARBY MECHANICS  (Emergency → Mechanics tab)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def emergency_mechanics_view(request):
    """
    Returns a list of available mechanics sorted by distance from user.

    Query parameters (optional):
      ?lat=12.9716&lng=77.5946   ← user's GPS from browser
      ?specialization=battery    ← filter by type (battery/charger/general/tyre/motor)

    Response:
    [
      {
        "id": 1,
        "name": "Raju EV Mechanic",
        "phone": "+91 98765 43210",
        "specialization": "battery",
        "specialization_display": "Battery Specialist",
        "location_text": "Bhopal, MP Nagar",
        "distance": 1.3,
        "experience_years": 5,
        "is_available": true,
        "rating": "4.5",
        "review_count": 12
      }
    ]
    """
    mechanics = Mechanic.objects.all()

    # Optional filter by specialization
    spec = request.query_params.get('specialization')
    if spec:
        mechanics = mechanics.filter(specialization=spec)

    mechanics = list(mechanics)

    # Sort by distance if user location provided
    user_lat = request.query_params.get('lat')
    user_lng = request.query_params.get('lng')

    if user_lat and user_lng:
        try:
            lat = float(user_lat)
            lng = float(user_lng)
            for m in mechanics:
                if m.latitude and m.longitude:
                    m.distance = haversine_distance(lat, lng, m.latitude, m.longitude)
                else:
                    m.distance = 9999.0
            mechanics.sort(key=lambda m: (not m.is_available, m.distance))
        except ValueError:
            pass

    serializer = MechanicSerializer(mechanics, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# EMERGENCY STATIONS  (Emergency → Battery & Charger tab)
# ─────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def emergency_stations_view(request):
    """
    Returns nearby EV stations for emergency charging/battery help.
    Reuses the Station model — just adds emergency-specific distance sorting.

    Query parameters (optional):
      ?lat=&lng=           ← user GPS
      ?min_rating=4        ← minimum average stars (same as /api/stations/)
      ?sort=rating         ← highest rated first (with distance when lat/lng set)
    """
    stations = (
        Station.objects.filter(is_active=True)
        .select_related('owner')
        .annotate(
            avg_rating=Coalesce(Avg('reviews__rating'), Value(0.0), output_field=FloatField()),
            review_count=Count('reviews', distinct=True),
        )
    )

    min_rating = request.query_params.get('min_rating')
    if min_rating:
        try:
            stations = stations.filter(avg_rating__gte=float(min_rating))
        except ValueError:
            pass

    sort_mode = (request.query_params.get('sort') or '').lower()
    user_lat = request.query_params.get('lat')
    user_lng = request.query_params.get('lng')
    stations_list = None

    if user_lat and user_lng:
        try:
            lat = float(user_lat)
            lng = float(user_lng)
            stations_list = sort_stations_by_distance(stations, lat, lng)
            if sort_mode == 'rating':
                stations_list.sort(
                    key=lambda s: (-float(getattr(s, 'avg_rating', 0) or 0), s.distance)
                )
        except ValueError:
            stations_list = None

    if stations_list is None:
        if sort_mode == 'rating':
            stations_list = list(stations.order_by('-avg_rating', 'name'))
        else:
            stations_list = list(stations.order_by('name'))

    serializer = StationSerializer(stations_list, many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
