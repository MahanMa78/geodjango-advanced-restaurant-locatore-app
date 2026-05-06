# restaurants/management/commands/import_osm_restaurants.py

import requests
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from restaurants.models import Restaurant, Category

class Command(BaseCommand):
    help = 'Import real restaurants from OpenStreetMap via Overpass API'

    def handle(self, *args, **options):
        self.stdout.write('Fetching restaurants from OpenStreetMap...')

        # Overpass query — restaurants in Lagos
        query = """
        [out:json][timeout:30];
        (
          node["amenity"="restaurant"](6.3,3.1,6.7,3.7);
          node["amenity"="fast_food"](6.3,3.1,6.7,3.7);
        );
        out body;
        """

        res = requests.get(
            'https://overpass-api.de/api/interpreter',
            params={'data': query},
            headers={
                'User-Agent': 'GeoDjango Restaurant Locator',
                'Accept': 'application/json',
            },
            timeout=60
        )
        if res.status_code != 200:
            self.stderr.write(f'Error fetching data: {res.status_code}')
            self.stdout.write(res.text[:300])
            return
        try:
            data = res.json()
        except Exception:
            self.stderr.write('Error parsing JSON response')
            self.stdout.write(res.text[:300])
            return
        elements = data.get('elements', [])
        self.stdout.write(f'Found {len(elements)} places from OSM')

        default_cat, _ = Category.objects.get_or_create(
            name='Restaurant', defaults={'icon': '🍽️'}
        )

        created = 0
        for el in elements:
            tags = el.get('tags', {})
            name = tags.get('name')
            if not name:
                continue  # skip unnamed places

            lat = el.get('lat')
            lon = el.get('lon')
            if not lat or not lon:
                continue

            Restaurant.objects.get_or_create(
                name=name,
                defaults={
                    'address':          tags.get('addr:street', 'Lagos, Nigeria'),
                    'location':         Point(lon, lat, srid=4326),
                    'category':         default_cat,
                    'rating':           4.0,
                    'price_range':      2,
                    'delivery_time_min': 30,
                    'delivery_fee':     500,
                    'minimum_order':    1000,
                    'is_open':          True,
                }
            )
            created += 1

        self.stdout.write(f'✅ Imported {created} restaurants from OpenStreetMap')