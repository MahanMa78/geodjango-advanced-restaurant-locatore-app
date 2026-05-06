import type { ReactNode } from 'react';
import type { Concept } from '../types';

const CONCEPTS: Concept[] = [
  {
    icon: '🗄️', color: '#EFF6FF',
    title: 'Spatial Database', subtitle: 'PostgreSQL + PostGIS',
    body: 'GeoDjango requires a spatially-enabled database. PostGIS adds geometry column types, spatial functions (ST_Distance, ST_Within), and GIST indexes to PostgreSQL.',
    code: `# settings.py
DATABASES = {
    'default': {
        # ← Key change from normal Django
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'nearme_db',
        'USER': 'postgres',
        'HOST': 'localhost',
    }
}
# Enables ST_Distance, ST_Within, ST_Intersects…`,
    api: null,
  },
  {
    icon: '📍', color: '#FFF7ED',
    title: 'PointField', subtitle: 'Store a GPS location',
    body: 'PointField stores latitude/longitude as a native geometry object. geography=True enables accurate spherical distance calculations — the Earth is not flat!',
    code: `# restaurants/models.py
from django.contrib.gis.db import models  # ← gis!

class Restaurant(models.Model):
    name = models.CharField(max_length=150)

    # geography=True → accurate spherical math
    # srid=4326     → WGS84 (GPS standard)
    location = models.PointField(
        srid=4326, geography=True,
    )

# Point(longitude, latitude) ← lng first!
r.location = Point(3.3792, 6.5244, srid=4326)`,
    api: '/api/restaurants/?format=json',
  },
  {
    icon: '⭕', color: '#F0FDF4',
    title: 'Radius Query', subtitle: 'distance_lte lookup',
    body: 'Find all restaurants within N km of a user. GeoDjango translates this into a PostGIS ST_DWithin() call with automatic unit handling via the D() measurement class.',
    code: `from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance

user_location = Point(3.3792, 6.5244, srid=4326)

# Core spatial query → ST_DWithin(location, point, 5000)
qs = Restaurant.objects.filter(
    location__distance_lte=(user_location, D(km=5))
).annotate(
    distance=Distance('location', user_location)
).order_by('distance')`,
    api: '/api/restaurants/nearby/?lat=6.5244&lng=3.3792&radius=5',
  },
  {
    icon: '🔷', color: '#FFF0F6',
    title: 'PolygonField', subtitle: 'Store area boundaries',
    body: 'Delivery zones are stored as Polygon geometries. The first and last coordinate must be identical to close the shape. GeoDjango serializes them to GeoJSON for Leaflet.',
    code: `# zones/models.py
class DeliveryZone(models.Model):
    area = models.PolygonField(srid=4326, geography=True)

# Creating a polygon:
from django.contrib.gis.geos import Polygon

zone = Polygon([
    (3.35, 6.50),  # (longitude, latitude)
    (3.40, 6.50),
    (3.40, 6.55),
    (3.35, 6.55),
    (3.35, 6.50),  # ← must close the ring
], srid=4326)`,
    api: '/api/zones/',
  },
  {
    icon: '🎯', color: '#F5F3FF',
    title: 'Containment', subtitle: 'area__contains lookup',
    body: "Check if a user's point falls inside a polygon delivery zone. Uses PostGIS ST_Contains(). Powers the live zone indicator in this app.",
    code: `from django.contrib.gis.geos import Point

user_point = Point(3.3792, 6.5244, srid=4326)

# → ST_Contains(zone.area, user_point)
zones = DeliveryZone.objects.filter(
    is_active=True,
    area__contains=user_point,
)

# ⚠️ Direction matters:
# area__contains=point → zone CONTAINS point ✓
# area__within=point   → zone is INSIDE point ✗`,
    api: '/api/zones/check/?lat=6.5244&lng=3.3792',
  },
  {
    icon: '🔀', color: '#ECFDF5',
    title: 'Intersection', subtitle: 'area__intersects lookup',
    body: 'Checks if two geometries share any space. Used for detecting overlapping delivery zones and route conflicts.',
    code: `ref = DeliveryZone.objects.get(id=1)

# → ST_Intersects(zone.area, ref.area)
overlapping = DeliveryZone.objects.filter(
    area__intersects=ref.area
).exclude(id=1)

# Other spatial lookups:
# location__within=polygon → ST_Within
# area__touches=other      → ST_Touches`,
    api: '/api/zones/overlapping/?zone_id=1',
  },
  {
    icon: '📐', color: '#FFFBEB',
    title: 'Measurement', subtitle: 'D() and Distance()',
    body: 'The D() class creates unit-aware distance objects. GeoDjango converts them to the correct database unit automatically.',
    code: `from django.contrib.gis.measure import D

D(km=5)   # → 5000 m to PostGIS
D(mi=3)   # → 4828 m to PostGIS
D(m=500)  # → 500 m to PostGIS

# Convert between units freely
d = D(km=5)
d.m   # → 5000.0
d.mi  # → 3.11

# After annotating with Distance():
obj.distance.km  # distance in kilometres`,
    api: null,
  },
  {
    icon: '🌐', color: '#F8FAFC',
    title: 'GeoJSON API', subtitle: 'GeoFeatureModelSerializer',
    body: 'djangorestframework-gis serializes your models to GeoJSON FeatureCollection format automatically. Leaflet reads this directly — no manual coordinate extraction needed.',
    code: `from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer
)

class RestaurantSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Restaurant
        geo_field = 'location'  # → becomes geometry
        fields = ['id', 'name', 'rating', ...]

# Output:
# { "type": "FeatureCollection", "features": [{
#   "type": "Feature",
#   "geometry": { "type": "Point",
#     "coordinates": [3.3792, 6.5244] },
#   "properties": { "name": "Mama Cass" }
# }]}`,
    api: '/api/restaurants/',
  },
  {
    icon: '🗺️', color: '#F0F9FF',
    title: 'Coordinate Systems', subtitle: 'SRID 4326 & projections',
    body: 'SRID 4326 (WGS84) is the GPS standard — degrees. For accurate area, transform to a metric CRS. geography=True handles spherical math for distances without transforms.',
    code: `# SRID 4326 = WGS84 (GPS degrees)
point = Point(3.3792, 6.5244, srid=4326)

# Transform for accurate area
zone = DeliveryZone.objects.get(id=1)
projected = zone.area.transform(32632, clone=True)
area_km2 = projected.area / 1_000_000

# geography=True handles spherical distance
class Restaurant(models.Model):
    location = models.PointField(
        srid=4326,
        geography=True,  # ← spherical math
    )`,
    api: null,
  },
  {
    icon: '🖥️', color: '#FDF4FF',
    title: 'GeoDjango Admin', subtitle: 'Map widgets for free',
    body: 'GISModelAdmin replaces admin.ModelAdmin and renders every geometry field as an interactive OpenLayers map — click to place points, draw polygons.',
    code: `# admin.py
from django.contrib.gis import admin  # ← gis!

@admin.register(Restaurant)
class RestaurantAdmin(admin.GISModelAdmin):
    list_display = ['name', 'category', 'rating']
    # 'location' PointField → click-to-place map widget

@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.GISModelAdmin):
    # 'area' PolygonField → draw tool on the map
    map_width  = 900
    map_height = 600`,
    api: null,
  },
  {
    icon: '📦', color: '#F0FDF4',
    title: 'GDAL Import', subtitle: 'Shapefiles & GeoJSON',
    body: 'GDAL reads real-world GIS datasets. Government portals distribute city boundaries, LGA areas, and road networks as Shapefiles.',
    code: `from django.contrib.gis.gdal import DataSource

ds = DataSource('/data/nga_adm1.shp')
layer = ds[0]

print(layer.geom_type)  # MultiPolygon
print(layer.fields)     # ['NAME_1', 'ISO', …]

for feature in layer:
    State.objects.get_or_create(
        name=feature['NAME_1'].value,
        defaults={
            'boundary': feature.geom.geos,
        }
    )`,
    api: null,
  },
  {
    icon: '🏗️', color: '#FFF7ED',
    title: 'Full Stack Flow', subtitle: 'How it all connects',
    body: 'React + Leaflet on the frontend, GeoJSON over HTTP, GeoDjango ORM for spatial queries, PostGIS for storage, GEOS + GDAL as the geometry engine.',
    code: `# 1. React sends user location
GET /api/restaurants/nearby/?lat=6.52&lng=3.38

# 2. GeoDjango queries PostGIS
user_pt = Point(3.38, 6.52, srid=4326)
qs = Restaurant.objects.filter(
    location__distance_lte=(user_pt, D(km=5))
).annotate(distance=Distance('location', user_pt))

# 3. GeoFeatureModelSerializer → GeoJSON
# 4. Leaflet renders markers from geometry
restaurants.map(r => (
  <Marker position={[r.lat, r.lng]} />
))`,
    api: null,
  },
];

// ── Main component ─────────────────────────────────────────

export default function ConceptsView(): ReactNode {
  return (
    <div className="flex-1 overflow-y-auto scrollbar-thin bg-surface">
      {/* Page header */}
      <div className="px-8 pt-8 pb-6 border-b border-edge bg-white sticky top-0 z-10">
        <h2 className="text-2xl font-bold text-ink mb-1" style={{ fontFamily: 'Syne, sans-serif' }}>
          GeoDjango Concepts
        </h2>
        <p className="text-sm text-ink-muted">
          Every spatial concept used in this app — with the exact backend code that powers it.
        </p>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-4 p-6">
        {CONCEPTS.map((c, i) => (
          <ConceptCard key={i} concept={c} />
        ))}
      </div>
    </div>
  );
}

// ── Concept card ───────────────────────────────────────────

function ConceptCard({ concept }: { concept: Concept }): ReactNode {
  const { icon, color, title, subtitle, body, code, api } = concept;

  return (
    <div className="bg-white border border-edge rounded-2xl overflow-hidden flex flex-col hover:shadow-panel transition-shadow duration-200">
      {/* Card header */}
      <div className="flex items-start gap-3 px-5 pt-5 pb-4">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0"
          style={{ background: color }}
        >
          {icon}
        </div>
        <div>
          <p className="font-bold text-sm text-ink leading-snug" style={{ fontFamily: 'Syne, sans-serif' }}>
            {title}
          </p>
          <p className="text-xs text-ink-faint mt-0.5">{subtitle}</p>
        </div>
      </div>

      {/* Body */}
      <p className="text-xs text-ink-muted leading-relaxed px-5 pb-4">{body}</p>

      {/* Code block */}
      <div
        className="mx-4 mb-4 rounded-xl overflow-x-auto"
        style={{ background: '#1A1A18' }}
      >
        <pre className="p-4 text-[11px] leading-relaxed text-[#E8E5D8] m-0 overflow-x-auto"
          style={{ fontFamily: 'JetBrains Mono, monospace' }}>
          <CodeHighlight code={code} />
        </pre>
      </div>

      {/* API link */}
      {api && (
        <div className="px-5 pb-4 mt-auto">
          <a
            href={api}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-[11px] text-blue-600 no-underline hover:underline"
            style={{ fontFamily: 'JetBrains Mono, monospace' }}
          >
            🔗 <span className="opacity-70">Try live:</span> {api}
          </a>
        </div>
      )}
    </div>
  );
}

// ── Code highlighter ───────────────────────────────────────

function CodeHighlight({ code }: { code: string }): ReactNode {
  const lines = code.split('\n').map((line, i) => {
    if (line.trim().startsWith('#') || line.trim().startsWith('//')) {
      return <div key={i} className="code-comment">{line || '\u00A0'}</div>;
    }

    const html = line
      .replace(/(from|import|class|def|return|if|else|for|in|not|and|or|True|False|None|GET)\b/g,
        '<span class="code-keyword">$1</span>')
      .replace(/'([^']*)'/g, "<span class='code-string'>'$1'</span>")
      .replace(/"([^"]*)"/g, '<span class="code-string">"$1"</span>')
      .replace(/\b(models|objects|filter|annotate|exclude|get|create|order_by|transform|distance)\b/g,
        '<span class="code-func">$1</span>')
      .replace(/\b(Restaurant|DeliveryZone|Point|Polygon|D|Distance|DataSource|GeoFeatureModelSerializer)\b/g,
        '<span class="code-class">$1</span>');

    return <div key={i} dangerouslySetInnerHTML={{ __html: html || '\u00A0' }} />;
  });

  return <>{lines}</>;
}