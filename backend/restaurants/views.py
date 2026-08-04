"""
restaurants/views.py

GEODJANGO CONCEPTS DEMONSTRATED:
  1. distance_lte — find restaurants within a radius
  2. Distance annotation — annotate queryset with distance from user
  3. D() measurement — unit-aware distance objects
  4. Point() — create a geometry from coordinates
  5. geography=True distance accuracy
  6. Ordering by distance
"""

from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.shortcuts import get_object_or_404


from rest_framework import viewsets, status
from rest_framework.decorators import action , api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Restaurant, Category, MenuItem
from .serializers import (
    RestaurantListSerializer,
    RestaurantDetailSerializer, 
    RestaurantWriteSerializer,
    CategorySerializer,
    MenuItemSerializer,
)
from .services import OSRMRoutingService
from .pricing_service import DynamicPricingService
from .geocoding_service import NominatimGeocodingService


class RestaurantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Restaurant CRUD + Spatial Queries
    
    Routes:
      GET  /api/restaurants/                → list (GeoJSON FeatureCollection)
      POST /api/restaurants/                → create
      GET  /api/restaurants/<id>/           → detail (GeoJSON Feature)
      PUT  /api/restaurants/<id>/           → update
      DEL  /api/restaurants/<id>/           → delete
      GET  /api/restaurants/nearby/         → SPATIAL: radius search
      GET  /api/restaurants/bbox/           → SPATIAL: bounding box search
      GET  /api/restaurants/categories/     → list all categories
    """
    queryset = Restaurant.objects.select_related('category').all()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RestaurantDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return RestaurantWriteSerializer
        return RestaurantListSerializer
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category__name__icontains=category)
        
        # Filter by open status
        is_open = self.request.query_params.get('is_open')
        if is_open is not None:
            qs = qs.filter(is_open=(is_open.lower() == 'true'))
        
        # Filter by price range
        price = self.request.query_params.get('price_range')
        if price:
            qs = qs.filter(price_range=price)
        
        # Text search
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        
        return qs
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        ════════════════════════════════════════════════════════
        GEODJANGO CORE CONCEPT: Spatial Radius Query
        ════════════════════════════════════════════════════════
        
        Find all restaurants within a given radius of a point.
        
        Query params:
          lat     — user's latitude  (required)
          lng     — user's longitude (required)
          radius  — search radius in km (default: 5)
          
        Example: /api/restaurants/nearby/?lat=6.5244&lng=3.3792&radius=5
        
        How it works:
        
        1. Create a Point geometry from the user's coordinates
           Point(longitude, latitude) ← note: lng first!
        
        2. Use distance_lte lookup to filter:
           location__distance_lte=(point, D(km=radius))
           
           This translates to PostGIS SQL:
           WHERE ST_DWithin(location, ST_GeomFromText('POINT(3.38 6.52)'), 5000)
           
           Because geography=True, the distance is in METERS on the sphere.
           D(km=5) automatically converts to 5000 meters.
        
        3. Annotate each result with its exact distance:
           annotate(distance=Distance('location', user_location))
           
           Distance() is a database function that calls ST_Distance()
           and attaches the result to each object as obj.distance
        
        4. Order by distance (closest first)
        
        5. Serialize to GeoJSON — the distance is included in properties
        """
        
        # Validate required params
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        if not lat or not lng:
            return Response(
                {'error': 'lat and lng query parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(lat)
            lng = float(lng)
            radius_km = float(request.query_params.get('radius', 5))
        except ValueError:
            return Response(
                {'error': 'lat, lng, and radius must be numeric'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # ─────────────────────────────────────────────
        # STEP 1: Create a Point from user's location
        # Point(longitude, latitude) — lng first!
        # srid=4326 tells PostGIS this is WGS84 (GPS) coordinates
        # ─────────────────────────────────────────────
        user_location = Point(lng, lat, srid=4326)
        
        # ─────────────────────────────────────────────
        # STEP 2: Spatial filter — distance_lte
        # D(km=radius_km) creates a Distance object in km
        # PostGIS handles the spherical math (because geography=True)
        # ─────────────────────────────────────────────
        qs = Restaurant.objects.filter(
            is_open=True,
            location__distance_lte=(user_location, D(km=radius_km))
        )
        
        # ─────────────────────────────────────────────
        # STEP 3: Annotate with actual distance
        # Distance() calls ST_Distance() in the database
        # obj.distance will be a Distance object you can call .km, .m on
        # ─────────────────────────────────────────────
        qs = qs.annotate(
            distance=Distance('location', user_location)
        ).order_by('distance')  # Closest first
        
        # Optional filters on top of spatial filter
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category__name__icontains=category)
        
        # Serialize to GeoJSON
        serializer = RestaurantListSerializer(
            qs, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bbox(self, request):
        """
        ════════════════════════════════════════════════════════
        GEODJANGO CONCEPT: Bounding Box Query
        ════════════════════════════════════════════════════════
        
        Find all restaurants within a bounding box (map viewport).
        Used when the user pans/zooms the map.
        
        Query params:
          min_lat, max_lat, min_lng, max_lng
          
        Example: /api/restaurants/bbox/?min_lat=6.4&max_lat=6.6&min_lng=3.2&max_lng=3.5
        """
        try:
            min_lat = float(request.query_params['min_lat'])
            max_lat = float(request.query_params['max_lat'])
            min_lng = float(request.query_params['min_lng'])
            max_lng = float(request.query_params['max_lng'])
        except (KeyError, ValueError):
            return Response(
                {'error': 'min_lat, max_lat, min_lng, max_lng are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # GEODJANGO: bbcontains — check if bounding box contains the point
        # This is faster than a full geometry check, good for viewport queries
        from django.contrib.gis.geos import Polygon
        
        bbox = Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))
        bbox.srid = 4326
        
        qs = Restaurant.objects.filter(
            location__within=bbox  # Exact containment (use bbcontains for faster approx)
        ).select_related('category')
        
        serializer = RestaurantListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """List all categories with restaurant counts"""
        cats = Category.objects.all()
        serializer = CategorySerializer(cats, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MenuItemViewSet(viewsets.ModelViewSet):
    serializer_class = MenuItemSerializer
    
    def get_queryset(self):
        return MenuItem.objects.filter(
            restaurant_id=self.kwargs['restaurant_pk']
        )
        
 
@api_view(['GET'])
def restaurant_route(request, pk):
    """
    Calculate real road-network route from user location to a specific restaurant.
    Query params required: ?user_lat=...&user_lng=...
    """
    user_lat = request.query_params.get('user_lat')
    user_lng = request.query_params.get('user_lng')

    if not user_lat or not user_lng:
        return Response(
            {'error': 'user_lat and user_lng query parameters are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user_lat = float(user_lat)
        user_lng = float(user_lng)
    except ValueError:
        return Response({'error': 'Invalid coordinates'}, status=status.HTTP_400_BAD_REQUEST)

    restaurant = get_object_or_404(Restaurant, pk=pk)

    """
    We need to start the route from the restaurant,
    and the endpoint should be the user's location.
    """
    route_result = OSRMRoutingService.get_route(
        start_lng=restaurant.longitude,
        start_lat=restaurant.latitude,
        end_lng=user_lng,
        end_lat=user_lat
    )

    if not route_result['success']:
        return Response({'error': route_result['error']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'restaurant_id': restaurant.id,
        'restaurant_name': restaurant.name,
        'distance_km': route_result['distance_km'],
        'duration_minutes': route_result['duration_minutes'],
        'route_geometry': route_result['geojson']  # GeoJSON LineString
    })


class RestaurantRouteView(APIView):
    """
    GET /api/restaurants/<id>/route/?user_lat=&user_lng=
    OSRM Route Calculation and Dynamic Delivery Pricing
    """
    def get(self, request, pk):
        user_lat = request.query_params.get('user_lat')
        user_lng = request.query_params.get('user_lng')

        if not user_lat or not user_lng:
            return Response(
                {"error": "The user_lat and user_lng parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_lat = float(user_lat)
            user_lng = float(user_lng)
        except ValueError:
            return Response(
                {"error": "The input coordinates are invalid."},
                status=status.HTTP_400_BAD_REQUEST
            )

        restaurant = get_object_or_404(Restaurant, pk=pk)

        # Get OSRM route (Origin: Restaurant | Destination: User)
        route_result = OSRMRoutingService.get_route(
            start_lng=restaurant.longitude,
            start_lat=restaurant.latitude,
            end_lng=user_lng,
            end_lat=user_lat
        )

        if not route_result.get("success"):
            return Response(
                {"error": route_result.get("error", "Error occurred while fetching the route")},
                status=status.HTTP_502_BAD_GATEWAY
            )

        distance_km = route_result["distance_km"]
        duration_minutes = route_result["duration_minutes"]

        # 🚀 Smart shipping cost calculation with DynamicPricingService
        pricing_breakdown = DynamicPricingService.calculate_delivery_fee(distance_km)

        return Response({
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "distance_km": distance_km,
            "duration_minutes": duration_minutes,
            "pricing": pricing_breakdown, # 👈 Complete invoice details added to the API response
            "route_geometry": route_result.get("geojson") or route_result.get("route_geometry")
        })


class ReverseGeocodeView(APIView):
    """
    GET /api/geocoding/reverse/?lat=36.27&lng=50.00
    تبدیل مختصات جغرافیایی به آدرس متنی قابل فهم
    """
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')

        if not lat or not lng:
            return Response(
                {"error": "پارامترهای lat و lng الزامی هستند."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response(
                {"error": "مختصات ورودی نامعتبر است."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = NominatimGeocodingService.reverse_geocode(lat, lng)

        if not result.get("success"):
            return Response(result, status=status.HTTP_502_BAD_GATEWAY)

        return Response(result)

class CreateOrderView(APIView):
    """
    POST /api/orders/create/
    Placing a new order and automatically executing the courier movement simulation in Celery.
    """
    def post(self, request):
        restaurant_id = request.data.get('restaurant_id')
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        address = request.data.get('address', '')
        total_amount = request.data.get('total_amount', 0)
        delivery_fee = request.data.get('delivery_fee', 0)

        if not all([restaurant_id, lat, lng]):
            return Response(
                {"error": "The parameters restaurant_id, lat, and lng are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response({"error": "Restaurant not found."}, status=status.HTTP_404_NOT_FOUND)

        # Create New Order
        order = Order.objects.create(
            restaurant=restaurant,
            delivery_location=Point(float(lng), float(lat), srid=4326),
            delivery_address=address,
            total_amount=total_amount,
            delivery_fee=delivery_fee,
            status='PREPARING'
        )

        # Calling async Celery task to simulate the movement of the pickaxe
        simulate_courier_movement.delay(order.id)

        return Response({
            "success": True,
            "order_id": order.id,
            "status": order.status,
            "message": "Order placed successfully and the courier will arrive soon."
        }, status=status.HTTP_201_CREATED)