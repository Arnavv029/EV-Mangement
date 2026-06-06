"""
Distance Calculator — Haversine Formula
=========================================
When a user opens the Home page, they share their GPS location.
We use their latitude/longitude to calculate the distance to each station.
This lets us show: "2.3 km away" on every station card.

HAVERSINE FORMULA:
  Calculates the straight-line distance between two points on Earth
  given their latitude and longitude. It accounts for Earth's curvature.

  Result is in KILOMETERS.

No external API (like Google Maps) is needed for this calculation.
It runs entirely on our server.
"""

import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance in kilometers between two GPS coordinates.

    Args:
        lat1, lon1: User's latitude and longitude
        lat2, lon2: Station's latitude and longitude

    Returns:
        float: Distance in kilometers (rounded to 2 decimal places)

    Example:
        distance = haversine_distance(12.9716, 77.5946, 12.9352, 77.6245)
        # Returns something like 4.72 (km)
    """

    # Earth's radius in kilometers
    R = 6371.0

    # Convert degrees to radians
    # (Math functions in Python use radians, not degrees)
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) *
         math.sin(delta_lon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c

    return round(distance, 2)


def sort_stations_by_distance(stations, user_lat, user_lon):
    """
    Takes a list of Station objects and adds 'distance' to each,
    then sorts them nearest-first.

    Args:
        stations: QuerySet of Station objects
        user_lat: User's current latitude
        user_lon: User's current longitude

    Returns:
        list: Stations with .distance attribute, sorted by proximity

    Example output:
        [
          { station: "Green Hub", distance: 1.2 },  ← nearest
          { station: "Power Point", distance: 3.5 },
          { station: "Charge Zone", distance: 8.1 },
        ]
    """
    stations_with_distance = []

    for station in stations:
        if station.latitude and station.longitude:
            # Calculate actual GPS distance
            dist = haversine_distance(
                user_lat, user_lon,
                station.latitude, station.longitude
            )
        else:
            # If the station has no GPS data, assign a large distance
            # so it appears at the bottom of the list
            dist = 9999.0

        # Attach distance as a temporary attribute to the station object
        station.distance = dist
        stations_with_distance.append(station)

    # Sort: smallest distance first
    stations_with_distance.sort(key=lambda s: s.distance)

    return stations_with_distance
