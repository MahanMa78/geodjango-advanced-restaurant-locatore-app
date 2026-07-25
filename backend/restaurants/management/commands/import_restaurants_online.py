# restaurants/management/commands/import_restaurants_online.py

import requests
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from restaurants.models import Restaurant, Category

class Command(BaseCommand):
    help = 'Import real restaurants from OpenStreetMap via Overpass API'

    def add_arguments(self, parser): 
        """
        A bounding box defines the minimum rectangular area that completely contains
        a geographic feature, using its minimum and maximum longitude and latitude.
        """
        parser.add_argument(
            '--bbox',
            type=str,
            default='36.24,49.95,36.32,50.08',
            help='Bounding box: min_lat,min_lon,max_lat,max_lon',
        )
        parser.add_argument(
            '--city',
            type=str,
            default='Qazvin, Iran',
            help='City name for default address',
        )
    
    def handle(self, *args, **options):
        bbox = options['bbox']
        city_name = options['city']
        
        self.stdout.write('Fetching restaurants from OpenStreetMap for bbox [{bbox}]...')

        # Overpass query — restaurants in Lagos
        query = f"""
        [out:json][timeout:30];
        (
          node["amenity"="restaurant"]({bbox});
          node["amenity"="fast_food"]({bbox});
          node["amenity"="cafe"]({bbox});
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
            self.stderr.write(self.style.ERROR(f'Error fetching data: {res.status_code}'))
            self.stdout.write(res.text[:300])
            return
        try:
            data = res.json()
        except Exception:
            self.stderr.write(self.style.ERROR('Error parsing JSON response'))
            self.stdout.write(res.text[:300])
            return
        elements = data.get('elements', [])
        self.stdout.write(self.style.SUCCESS(f'Found {len(elements)} places from OSM'))

        default_cat, _ = Category.objects.get_or_create(
            name='Restaurant', defaults={'icon': '🍽️'}
        )

        created = 0
        for el in elements:
            tags = el.get('tags', {})
            name = tags.get('name') or tags.get('name:fa') or tags.get('name:en')
            if not name:
                continue  # skip unnamed places

            lat = el.get('lat')
            lon = el.get('lon')
            if not lat or not lon:
                continue

            street = tags.get('addr:street') or tags.get('street') or city_name
            
            Restaurant.objects.get_or_create(
                name=name,
                defaults={
                    'address':          street,
                    'location':         Point(lon, lat, srid=4326),
                    'category':         default_cat,
                    'rating':           4.0,
                    'price_range':      2,
                    'delivery_time_min': 30,
                    'delivery_fee':     15000,
                    'minimum_order':    50000,
                    'is_open':          True,
                }
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Imported {created} restaurants from OpenStreetMap'))