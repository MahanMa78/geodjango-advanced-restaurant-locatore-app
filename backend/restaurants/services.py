import requests
from django.contrib.gis.geos import LineString
import logging

logger = logging.getLogger(__name__)

class OSRMRoutingService:
    """
    Service helper to fetch real road-network routing data from OSRM engine.
    """

    OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"

    @classmethod
    def get_route(cls, start_lng: float, start_lat: float, end_lng: float, end_lat: float):
        """
        Fetches route geometry, distance (meters), and duration (seconds) between two points.
        Coordinates order in OSRM URL: longitude,latitude
        """
        url = f"{cls.OSRM_BASE_URL}/{start_lng},{start_lat};{end_lng},{end_lat}"
        params = {
            'overview': 'full',
            'geometries': 'geojson'
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 'Ok' and len(data.get('routes', [])) > 0:
                    route = data['routes'][0]
                    geometry_data = route['geometry']
                    
                    # Extract distance and duration information
                    distance_meters = route['distance']  # Metrics: meters
                    duration_seconds = route['duration']  # Metrics: seconds

                    # Convert GeoJSON coordinates to LineString in GeoDjango
                    coordinates = geometry_data['coordinates']
                    line_geometry = LineString(coordinates, srid=4326)

                    return {
                        'success': True,
                        'distance_meters': round(distance_meters, 2),
                        'distance_km': round(distance_meters / 1000, 2),
                        'duration_minutes': round(duration_seconds / 60),
                        'geometry': line_geometry,
                        'geojson': geometry_data
                    }
        except Exception as e:
            logger.error(f"OSRM Routing Error: {str(e)}")

        return {
            'success': False,
            'error': 'Failed to calculate route'
        }