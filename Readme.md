# NearMe — Full-Stack GeoDjango Restaurant Discovery Platform

> A production-ready geographic web application built with GeoDjango, PostGIS, React, Vite, and TypeScript. Find restaurants near you, visualize delivery zones, and run real spatial queries — all powered by PostGIS and displayed on a live Leaflet map.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5, GeoDjango, Django REST Framework |
| Spatial DB | PostgreSQL + PostGIS |
| Geo Libraries | GDAL, GEOS, PROJ |
| API | djangorestframework-gis (GeoJSON) |
| Frontend | React 18, Vite, TypeScript |
| Map | Leaflet, react-leaflet |
| Styling | Tailwind CSS |

---

## Prerequisites

Make sure these are installed on your system before anything else.

### macOS

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# System dependencies
brew install postgresql@15 postgis gdal geos proj

# Start PostgreSQL
brew services start postgresql@15
```

### Ubuntu / WSL2 (Windows)

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-pip python3-venv \
    postgresql postgresql-contrib \
    postgis postgresql-15-postgis-3 \
    binutils libproj-dev gdal-bin libgdal-dev python3-gdal

sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Windows (Native)

1. Install PostgreSQL from https://www.postgresql.org/download/windows/ — run **Stack Builder** after and install the PostGIS extension
2. Install OSGeo4W from https://trac.osgeo.org/osgeo4w/ — choose **Advanced Install** and select `gdal`, `geos`, `proj`
3. Add these paths to `backend/nearme/settings.py` (adjust version numbers to match your install):

```python
GDAL_LIBRARY_PATH = r'C:\OSGeo4W\bin\gdal309.dll'
GEOS_LIBRARY_PATH = r'C:\OSGeo4W\bin\geos_c.dll'
```

> **Tip:** WSL2 is much smoother on Windows. Run `wsl --install` in PowerShell as Administrator, then follow the Ubuntu steps above inside WSL2.

---

## Project Structure

```
nearme/
├── backend/
│   ├── nearme/               # Django project config
│   │   ├── settings.py       # PostGIS engine, CORS, DRF settings
│   │   └── urls.py
│   ├── restaurants/          # Core app — PointField models + spatial views
│   │   ├── models.py         # Restaurant (PointField), Category, MenuItem
│   │   ├── serializers.py    # GeoFeatureModelSerializer → GeoJSON
│   │   ├── views.py          # nearby(), bbox() spatial query endpoints
│   │   ├── admin.py          # GISModelAdmin with map widgets
│   │   └── management/
│   │       └── commands/
│   │           ├── seed_data.py              # Create sample Lagos data
│   │           └── import__restaurants_online.py # Pull real data from OSM
│   ├── zones/                # Delivery zones — PolygonField + containment
│   ├── requirements.txt
└── frontend/
    ├── src/
    │   ├── types.ts           # All TypeScript interfaces
    │   ├── api.ts             # Typed API layer + GeoJSON parsers
    │   ├── App.tsx
    │   └── components/
    │       ├── MapView.tsx         # Leaflet map + spatial query controls
    │       ├── RestaurantSidebar.tsx
    │       ├── DetailPanel.tsx
    │       └── ConceptsView.tsx    # Interactive GeoDjango reference
    ├── tailwind.config.js
    ├── vite.config.ts
    └── package.json
```

---

## Backend Setup

### 1. Create the PostGIS database

```bash
# macOS
psql postgres

# Ubuntu / WSL2
sudo -u postgres psql
```

```sql
CREATE USER restaurant_locator_user WITH PASSWORD 'restaurant_locator_pass';
CREATE DATABASE restaurant_locator OWNER restaurant_locator_user;
\c restaurant_locator_db
CREATE EXTENSION postgis;

-- Verify
SELECT postgis_version();
\q
```

### 2. Configure environment

```bash
cd backend


### 3. Install Python dependencies

```bash
# Create and activate virtual environment
python3 -m venv geoenv
source geoenv/bin/activate        # macOS / Linux / WSL2
# geoenv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 4. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Load data

**Option A — Seed with sample Lagos data (fastest):**

```bash
python manage.py seed_data
```

Creates 10 restaurants with real Lagos coordinates, 3 delivery zone polygons, menu items, and a Lagos MultiPolygon service area.

**Option B — Import real restaurants from OpenStreetMap:**

```bash
python manage.py import_restaurants_online
```

Pulls real restaurant names and coordinates from the OSM Overpass API and reverse-geocodes their addresses via Nominatim. Requires an internet connection.

### 6. Create admin user

```bash
python manage.py createsuperuser
```

### 7. Start the server

```bash
python manage.py runserver
```

API is live at **http://localhost:8000**

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

App is live at **http://localhost:5173**

> Both the Django server and the Vite dev server must be running at the same time. The Vite proxy forwards `/api/*` requests to `localhost:8000` automatically.

---

## API Reference

### Restaurants

```
GET  /api/restaurants/
     All restaurants as GeoJSON FeatureCollection

GET  /api/restaurants/:id/
     Single restaurant with menu items

GET  /api/restaurants/nearby/?lat=&lng=&radius=
     Spatial: restaurants within radius km (distance_lte)

GET  /api/restaurants/bbox/?min_lat=&max_lat=&min_lng=&max_lng=
     Spatial: restaurants within map viewport (within)

GET  /api/categories/
     All food categories
```

### Delivery Zones

```
GET  /api/zones/
     All delivery zones as GeoJSON polygons

GET  /api/zones/check/?lat=&lng=
     Spatial: which zones contain this point (area__contains)

GET  /api/zones/overlapping/?zone_id=
     Spatial: zones that intersect a given zone (area__intersects)
```

### Example spatial queries

```bash
# Restaurants within 5km of Victoria Island
curl "http://localhost:8000/api/restaurants/nearby/?lat=6.4281&lng=3.4273&radius=5"

# Check if a point is inside a delivery zone
curl "http://localhost:8000/api/zones/check/?lat=6.43&lng=3.42"
```

---

## Django Admin

Visit **http://localhost:8000/admin/** and log in with your superuser credentials.

- **Restaurants** — uses `GISModelAdmin`: the `location` PointField renders as a click-to-place map widget
- **Delivery Zones** — the `area` PolygonField renders as a draw tool so you can create zone boundaries directly on the map

---

## GeoDjango Concepts Covered

| Concept | Where to find it |
|---|---|
| `PointField` with `geography=True` | `restaurants/models.py` |
| `PolygonField` + `MultiPolygonField` | `zones/models.py` |
| Radius query — `distance_lte` | `restaurants/views.py → nearby()` |
| Distance annotation — `Distance()` | `restaurants/views.py → nearby()` |
| Containment — `area__contains` | `zones/views.py → check()` |
| Intersection — `area__intersects` | `zones/views.py → overlapping()` |
| GeoJSON serialization | `restaurants/serializers.py` |
| GDAL Shapefile import | `restaurants/management/commands/` |
| `GISModelAdmin` map widgets | `restaurants/admin.py` |
| Creating Point/Polygon in Python | `seed_data.py` |
| SRID + coordinate systems | `models.py`, `seed_data.py` |

---

## Common Errors

**`GDAL_ERROR: Could not find GDAL library`** — macOS Apple Silicon:
```python
# Add to settings.py
GDAL_LIBRARY_PATH = '/opt/homebrew/lib/libgdal.dylib'
GEOS_LIBRARY_PATH = '/opt/homebrew/lib/libgeos_c.dylib'
```

**`relation does not exist`** — migrations not run:
```bash
python manage.py migrate
```

**`could not open extension control file "postgis.control"`** — PostGIS not installed for your PostgreSQL version:
```bash
# macOS
brew install postgis

# Ubuntu
sudo apt-get install postgresql-15-postgis-3
```

**Frontend shows no restaurants** — verify data exists:
```bash
python manage.py shell -c "from restaurants.models import Restaurant; print(Restaurant.objects.count())"
# Must be greater than 0
```

**Admin map shows 403 Access Blocked** — OSM blocks localhost referers. This is a known OSM tile policy restriction for local development and does not affect the frontend map.

---

## Preparing for GitHub

Before pushing, make sure these are in your `.gitignore`:

```gitignore
# Python
geoenv/
__pycache__/
*.pyc
*.pyo
.env

# Django
staticfiles/
media/

# Node
node_modules/
dist/

# OS
.DS_Store
Thumbs.db
```

Generate a fresh secret key for your `.env`:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## License

MIT