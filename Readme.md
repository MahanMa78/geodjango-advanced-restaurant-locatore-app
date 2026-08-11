Markdown

````
# NearMe — Advanced Enterprise Web GIS & Live Courier Tracking Platform

> A production-ready, fully dockerized geographic web application built with GeoDjango, PostGIS, React, Vite, and TypeScript. Search restaurants, calculate OSRM road routes, calculate dynamic delivery fees, track couriers live via WebSockets & Celery, and execute sub-10ms spatial queries powered by Redis Geohash Caching.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0, GeoDjango, Django REST Framework |
| Spatial DB | PostgreSQL 15 + PostGIS |
| Geo Libraries | GDAL, GEOS, PROJ, djangorestframework-gis |
| Real-Time & Tasks | Django Channels (WebSockets), Celery, Daphne |
| Caching & Broker | Redis (Spatial Geohash Cache + Channel Layers) |
| Routing & Geocoding | OSRM Engine (Road Routing), Nominatim API (Reverse Geocode) |
| Frontend | React 18, Vite, TypeScript |
| Map | Leaflet.js, react-leaflet |
| Styling | Tailwind CSS |
| Infrastructure | Docker & Docker Compose |

---

## Prerequisites

Make sure Docker and Docker Compose are installed on your system before anything else.

### Docker Environment

Ensure Docker Daemon is active on your machine:

```bash
# Verify Docker Installation
docker --version
docker compose version
````

## Project Structure

Plaintext

```
geodjango-advanced-restaurant-locatore-app/
├── backend/
│   ├── backend/               # Django core setup (settings, asgi, urls)
│   ├── restaurants/           # Main GIS Application
│   │   ├── models.py          # Restaurant (PointField), Order, Courier, MenuItem
│   │   ├── serializers.py     # GeoJSON serializers
│   │   ├── views.py           # APIViews & ViewSets (nearby, bbox, route, order)
│   │   ├── utils.py           # Redis Geohash spatial caching strategy
│   │   ├── services.py        # OSRM Routing & Nominatim Geocoding services
│   │   ├── pricing_service.py # Dynamic Delivery Pricing Engine
│   │   ├── tasks.py           # Celery background task for courier simulation
│   │   ├── consumers.py       # WebSocket consumers for real-time tracking
│   │   └── management/
│   │       └── commands/
│   │           ├── seed_data.py              # Create sample delivery zones & data
│   │           └── import_restaurants_online.py # Pull real data from OSM
│   ├── zones/                 # Delivery Zones (PolygonField + Containment)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # MapView, OrderTracking, DetailPanel, Sidebar
│   │   ├── api.ts             # Axios API client & GeoJSON interfaces
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml         # Container orchestration (web, db, redis, celery)
└── README.md
```

## Docker Setup & Quick Start

### 1. Build and Start Docker Containers

Bash

```
docker compose up -d --build
```

### 2. Run Database Migrations

Bash

```
docker compose exec web python manage.py migrate
```

### 3. Load Data

**Option A — Import real restaurants from OpenStreetMap (Overpass API):**

Bash

```
docker compose exec web python manage.py import_restaurants_online
```

_Pulls real restaurant names and coordinates from OSM Overpass API for Qazvin city._

**Option B — Seed with sample data and delivery zones:**

Bash

```
# Seed Qazvin city with 2.0 km radius zones
docker compose exec web python manage.py seed_data --city "Qazvin" --radius-km 2.0 --reseed
```

### 4. Create Admin User

Bash

```
docker compose exec web python manage.py createsuperuser
```

### 5. Access Services

- **Frontend Web App:** `http://localhost:5173`
    
- **Django REST API:** `http://localhost:8000/api/`
    
- **Admin Dashboard:** `http://localhost:8000/admin/`
    

## API Reference

### Restaurants & Spatial Queries

Plaintext

```
GET  /api/restaurants/
     All restaurants as GeoJSON FeatureCollection

GET  /api/restaurants/:id/
     Single restaurant with menu items

GET  /api/restaurants/nearby/?lat=&lng=&radius=
     Spatial: restaurants within radius km (distance_lte with Redis Geohash Cache)

GET  /api/restaurants/bbox/?min_lat=&max_lat=&min_lng=&max_lng=
     Spatial: restaurants within map viewport (within)

GET  /api/restaurants/:id/route/?user_lat=&user_lng=
     Spatial Routing: OSRM road network geometry + Dynamic Delivery Pricing
```

### Delivery Zones & Geocoding

Plaintext

```
GET  /api/zones/
     All delivery zones as GeoJSON polygons

GET  /api/zones/check/?lat=&lng=
     Spatial: which zones contain this point (area__contains)

GET  /api/geocoding/reverse/?lat=&lng=
     Reverse Geocode coordinates to street address via Nominatim API
```

### Orders & Real-time Courier Tracking

Plaintext

```
POST /api/orders/create/
     Place new order & trigger Celery courier tracking simulation

WS   /ws/orders/:order_id/
     WebSocket channel for live sub-second courier coordinate updates
```

### Example Spatial Queries

Bash

```
# Nearby restaurants within 5km radius
curl "http://localhost:8000/api/restaurants/nearby/?lat=36.27&lng=50.00&radius=5"

# Calculate OSRM route & delivery fees for Restaurant 12
curl "http://localhost:8000/api/restaurants/12/route/?user_lat=36.2750&user_lng=50.0050"

# Reverse geocode location
curl "http://localhost:8000/api/geocoding/reverse/?lat=36.2688&lng=50.0041"
```

## Django Admin & QGIS Integration

### Django Admin

Visit **http://localhost:8000/admin/** and log in with your superuser credentials.

- **Restaurants:** Uses `GISModelAdmin` — the `location` PointField renders as a click-to-place map widget.
    
- **Delivery Zones:** The `area` PolygonField renders as a draw tool so you can create zone boundaries directly on the map.
    
- **Pricing Config:** Manage `base_fee`, `per_km_rate`, and peak hour multipliers dynamically without code changes.
    

### QGIS Integration (Spatial Analysis)

You can connect **QGIS** directly to the PostgreSQL/PostGIS database running inside Docker:

1. Open QGIS $\rightarrow$ Browser Panel $\rightarrow$ Right-click **PostgreSQL** $\rightarrow$ **New Connection**.
    
2. **Host:** `localhost` | **Port:** `5432` | **Database:** `mygeodb` | **Username:** `myprojectuser` | **Password:** `mypassword`
    
3. Open `restaurants_restaurant` layer to view attribute tables, edit points, and perform spatial analytics.
    

## GeoDjango Concepts Covered

|**Concept**|**Where to find it**|
|---|---|
|`PointField` with `geography=True`|`restaurants/models.py`|
|`PolygonField` + `MultiPolygonField`|`zones/models.py`|
|Radius query — `distance_lte`|`restaurants/views.py → nearby()`|
|Spatial Indexing — `GISTIndex`|PostgreSQL / PostGIS DB Layer|
|OSRM Road Network Routing|`restaurants/services.py → OSRMRoutingService`|
|Dynamic Delivery Pricing|`restaurants/pricing_service.py`|
|Reverse Geocoding|`restaurants/services.py → NominatimGeocodingService`|
|Real-time Tracking (WebSockets)|`restaurants/consumers.py` & `tasks.py`|
|Redis Spatial Caching|`restaurants/utils.py` (Geohash encoding)|

## Common Errors & Troubleshooting

- **WebSocket Timeout Error / Courier Icon Not Moving:** Occurs when Celery worker lacks dependencies. Rebuild containers:
    
    Bash
    
    ```
    docker compose down
    docker compose up -d --build
    ```
    
- **Nominatim 502 Bad Gateway / DNS Error:** Resolved by setting Google DNS (`8.8.8.8`) inside `docker-compose.yml`.
    
- **OSRM Road Route Direction Flipped:** OSRM requires origin point first (`restaurant`) and destination point second (`user`). Handled in `views.py`.
    

## License

MIT