"""
zones/views.py

GEODJANGO CONCEPTS:
  1. contains() — check if a polygon contains a point
  2. intersects() — check if two geometries overlap
  3. PolygonField GeoJSON serialization
  4. Area calculations
"""

from django.contrib.gis.geos import Point
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import DeliveryZoneSerializer, ServiceAreaSerializer

from .models import DeliveryZone, ServiceArea



class DeliveryZoneViewSet(viewsets.ModelViewSet):
    """
    CRUD for Delivery Zones + spatial queries.
    
    Routes:
      GET  /api/zones/                      → All zones (GeoJSON)
      GET  /api/zones/check/?lat=&lng=      → Which zone is this point in?
      GET  /api/zones/for_restaurant/<id>/  → Zones for a restaurant
    """
    serializer_class = DeliveryZoneSerializer
    
    def get_queryset(self):
        qs = DeliveryZone.objects.select_related('restaurant').filter(is_active=True)
        
        restaurant_id = self.request.query_params.get('restaurant')
        if restaurant_id:
            qs = qs.filter(restaurant_id=restaurant_id)
        
        return qs
    
    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        ════════════════════════════════════════════════════════
        GEODJANGO CORE CONCEPT: Containment Query
        ════════════════════════════════════════════════════════
        
        Check if a user's location falls within any delivery zone.
        
        Query params:
          lat — user's latitude
          lng — user's longitude
        
        Example: /api/zones/check/?lat=6.52&lng=3.38
        
        How it works:
        
        The lookup is: area__contains=user_point
        
        This translates to PostGIS:
          WHERE ST_Contains(area, ST_GeomFromText('POINT(3.38 6.52)', 4326))
        
        PostGIS checks each zone polygon and returns those where
        the point lies inside the polygon boundary.
        
        Key distinction:
          - area__contains(point) → the ZONE contains the POINT ✓
          - area__within(point)   → the ZONE is within the POINT ✗ (reversed!)
        """
        
        try:
            lat = float(request.query_params['lat'])
            lng = float(request.query_params['lng'])
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'lat and lng query parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create a Point from the user's location
        user_point = Point(lng, lat, srid=4326)
        
        # ─────────────────────────────────────────────
        # GEODJANGO: area__contains
        # Find all zones whose polygon contains this point.
        # Translates to: ST_Contains(zone.area, user_point)
        # ─────────────────────────────────────────────
        zones = DeliveryZone.objects.filter(
            is_active=True,
            area__contains=user_point  # ← Spatial containment
        ).select_related('restaurant')
        
        serializer = DeliveryZoneSerializer(
            zones, many=True, context={'request': request}
        )
        
        return Response({
            'point': {'lat': lat, 'lng': lng},
            'zones_found': zones.count(),
            'zones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def overlapping(self, request):
        """
        ════════════════════════════════════════════════════════
        GEODJANGO CONCEPT: Intersection Query
        ════════════════════════════════════════════════════════
        
        Find all zones that overlap with a given zone.
        Useful for detecting conflicting delivery areas.
        
        Query param: zone_id
        """
        zone_id = request.query_params.get('zone_id')
        if not zone_id:
            return Response({'error': 'zone_id required'}, status=400)
        
        try:
            reference_zone = DeliveryZone.objects.get(id=zone_id)
        except DeliveryZone.DoesNotExist:
            return Response({'error': 'Zone not found'}, status=404)
        
        # GEODJANGO: area__intersects
        # Find zones whose area overlaps with the reference zone's area.
        # Translates to: ST_Intersects(zone.area, reference_zone.area)
        overlapping = DeliveryZone.objects.filter(
            is_active=True,
            area__intersects=reference_zone.area  # ← Intersection check
        ).exclude(id=zone_id)  # Exclude the zone itself
        
        serializer = DeliveryZoneSerializer(
            overlapping, many=True, context={'request': request}
        )
        
        return Response({
            'reference_zone': reference_zone.name,
            'overlapping_count': overlapping.count(),
            'zones': serializer.data
        })


class ServiceAreaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ServiceArea.objects.filter(is_active=True)
    serializer_class = ServiceAreaSerializer