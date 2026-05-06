"""
Management command: python manage.py seed_data

Seeds the database with sample restaurants and delivery zones in Lagos, Nigeria.

GEODJANGO CONCEPTS DEMONSTRATED:
  1. Creating Point geometries programmatically
  2. Creating Polygon geometries (delivery zones)
  3. Using GEOS objects to create model instances
  4. SRID assignment
"""

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point, Polygon, MultiPolygon

from restaurants.models import Restaurant, Category, MenuItem
from zones.models import DeliveryZone, ServiceArea


class Command(BaseCommand):
    help = 'Seeds the database with sample restaurants and zones in Lagos'
    
    def handle(self, *args, **options):
        self.stdout.write('🌍 Seeding GeoDjango sample data for Lagos, Nigeria...\n')
        
        # Clear existing data
        DeliveryZone.objects.all().delete()
        MenuItem.objects.all().delete()
        Restaurant.objects.all().delete()
        Category.objects.all().delete()
        ServiceArea.objects.all().delete()
        
        # ─────────────────────────────────────────────────────────
        # GEODJANGO: Create categories
        # ─────────────────────────────────────────────────────────
        categories = {}
        category_data = [
            ('Nigerian', '🍲'),
            ('Pizza', '🍕'),
            ('Chinese', '🥡'),
            ('Burgers', '🍔'),
            ('Shawarma', '🌯'),
            ('Seafood', '🦐'),
            ('Drinks', '🥤'),
        ]
        for name, icon in category_data:
            cat = Category.objects.create(name=name, icon=icon)
            categories[name] = cat
        
        self.stdout.write('✅ Created categories')
        
        # ─────────────────────────────────────────────────────────
        # GEODJANGO: Creating Point geometries
        # Point(longitude, latitude) — always longitude first!
        #
        # These are real coordinates for Lagos landmarks.
        # We use srid=4326 (WGS84 / GPS coordinate system)
        # ─────────────────────────────────────────────────────────
        restaurants_data = [
            {
                'name': 'Mama Cass Restaurant',
                'description': 'Authentic Nigerian cuisine in the heart of VI. Known for egusi soup and jollof rice.',
                'address': '2 Oba Elegushi Road, Victoria Island, Lagos',
                'category': 'Nigerian',
                # Point(longitude, latitude) ← note the order
                'location': Point(3.4273, 6.4281, srid=4326),
                'rating': 4.6,
                'price_range': 2,
                'delivery_time_min': 35,
                'delivery_fee': 600,
                'minimum_order': 2000,
                'image_url': 'https://images.unsplash.com/photo-1567364816519-cbc9c4ffe5fb?w=400',
            },
            {
                'name': 'The Place Restaurant',
                'description': 'Popular Nigerian fast food chain. Great suya, rice dishes and fresh fish.',
                'address': '5A Admiralty Way, Lekki Phase 1, Lagos',
                'category': 'Nigerian',
                'location': Point(3.5020, 6.4455, srid=4326),
                'rating': 4.3,
                'price_range': 2,
                'delivery_time_min': 40,
                'delivery_fee': 700,
                'minimum_order': 1500,
                'image_url': 'https://images.unsplash.com/photo-1604329760661-e71dc83f8f26?w=400',
            },
            {
                'name': 'Domino\'s Pizza Ikeja',
                'description': 'Hot, fresh pizza delivered to your door. Classic and creative toppings.',
                'address': '18 Toyin Street, Ikeja, Lagos',
                'category': 'Pizza',
                'location': Point(3.3479, 6.5917, srid=4326),
                'rating': 4.1,
                'price_range': 2,
                'delivery_time_min': 30,
                'delivery_fee': 500,
                'minimum_order': 3000,
                'image_url': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400',
            },
            {
                'name': 'ChiChi Chinese Restaurant',
                'description': 'Authentic Cantonese cuisine. Dim sum, noodles, and seafood dishes.',
                'address': '23 Awolowo Road, Ikoyi, Lagos',
                'category': 'Chinese',
                'location': Point(3.4396, 6.4528, srid=4326),
                'rating': 4.4,
                'price_range': 3,
                'delivery_time_min': 45,
                'delivery_fee': 1000,
                'minimum_order': 5000,
                'image_url': 'https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400',
            },
            {
                'name': 'Burger King VI',
                'description': 'Flame-grilled burgers, crispy fries, and refreshing drinks.',
                'address': '1005 Adeola Odeku, Victoria Island, Lagos',
                'category': 'Burgers',
                'location': Point(3.4251, 6.4297, srid=4326),
                'rating': 4.0,
                'price_range': 2,
                'delivery_time_min': 25,
                'delivery_fee': 500,
                'minimum_order': 2000,
                'image_url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400',
            },
            {
                'name': 'Suya Spot Surulere',
                'description': 'Best suya in Lagos! Premium beef, chicken and ram suya grilled to perfection.',
                'address': '7 Adeniran Ogunsanya, Surulere, Lagos',
                'category': 'Nigerian',
                'location': Point(3.3579, 6.5004, srid=4326),
                'rating': 4.8,
                'price_range': 1,
                'delivery_time_min': 20,
                'delivery_fee': 300,
                'minimum_order': 1000,
                'image_url': 'https://images.unsplash.com/photo-1544025162-d76538b2ed11?w=400',
            },
            {
                'name': 'Ocean Basket',
                'description': 'Fresh seafood from South Africa. Prawns, calamari, fish and chips.',
                'address': 'The Palms Mall, Lekki, Lagos',
                'category': 'Seafood',
                'location': Point(3.4748, 6.4353, srid=4326),
                'rating': 4.5,
                'price_range': 3,
                'delivery_time_min': 50,
                'delivery_fee': 1200,
                'minimum_order': 6000,
                'image_url': 'https://images.unsplash.com/photo-1615141982883-c7ad0e69fd62?w=400',
            },
            {
                'name': 'Mr Biggs Yaba',
                'description': 'Nigerian fast food classic. Pies, meat pies, jollof rice, and cold drinks.',
                'address': '2 Herbert Macaulay Way, Yaba, Lagos',
                'category': 'Nigerian',
                'location': Point(3.3761, 6.5041, srid=4326),
                'rating': 3.8,
                'price_range': 1,
                'delivery_time_min': 25,
                'delivery_fee': 400,
                'minimum_order': 800,
                'image_url': 'https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?w=400',
            },
            {
                'name': 'Barcelos Lekki',
                'description': 'South African flame-grilled chicken. Peri-peri sauces and wraps.',
                'address': '19B Admiralty Way, Lekki Phase 1, Lagos',
                'category': 'Burgers',
                'location': Point(3.4989, 6.4432, srid=4326),
                'rating': 4.2,
                'price_range': 2,
                'delivery_time_min': 35,
                'delivery_fee': 800,
                'minimum_order': 3000,
                'image_url': 'https://images.unsplash.com/photo-1598514983318-2f64f8f4796c?w=400',
            },
            {
                'name': 'Nando\'s Ikeja City Mall',
                'description': 'Portuguese-inspired peri-peri chicken. Mild to extra hot.',
                'address': 'Ikeja City Mall, Obafemi Awolowo Way, Ikeja',
                'category': 'Burgers',
                'location': Point(3.3456, 6.6024, srid=4326),
                'rating': 4.3,
                'price_range': 2,
                'delivery_time_min': 30,
                'delivery_fee': 600,
                'minimum_order': 2500,
                'image_url': 'https://images.unsplash.com/photo-1598514983318-2f64f8f4796c?w=400',
            },
        ]
        
        restaurants = {}
        for data in restaurants_data:
            cat = categories[data.pop('category')]
            r = Restaurant.objects.create(category=cat, **data)
            restaurants[r.name] = r
        
        self.stdout.write(f'✅ Created {len(restaurants)} restaurants')
        
        # ─────────────────────────────────────────────────────────
        # GEODJANGO: Creating Polygon geometries (delivery zones)
        #
        # A Polygon is a list of coordinate tuples.
        # IMPORTANT: The first and last coordinate must be the same
        # to "close" the ring.
        #
        # Format: Polygon([(lng, lat), (lng, lat), ..., (lng, lat)])
        # ─────────────────────────────────────────────────────────
        
        # Delivery zone for Mama Cass (covers Victoria Island)
        vi_zone = Polygon([
            (3.410, 6.420),
            (3.450, 6.420),
            (3.450, 6.440),
            (3.410, 6.440),
            (3.410, 6.420),  # ← Close the ring
        ], srid=4326)
        
        DeliveryZone.objects.create(
            name='Victoria Island Zone',
            restaurant=restaurants['Mama Cass Restaurant'],
            area=vi_zone,
            delivery_fee=600,
            min_order=2000,
            estimated_time=30,
        )
        
        # Delivery zone for Suya Spot (covers Surulere)
        surulere_zone = Polygon([
            (3.340, 6.490),
            (3.380, 6.490),
            (3.380, 6.515),
            (3.340, 6.515),
            (3.340, 6.490),
        ], srid=4326)
        
        DeliveryZone.objects.create(
            name='Surulere Zone',
            restaurant=restaurants['Suya Spot Surulere'],
            area=surulere_zone,
            delivery_fee=300,
            min_order=1000,
            estimated_time=20,
        )
        
        # Delivery zone for Domino's Ikeja
        ikeja_zone = Polygon([
            (3.325, 6.575),
            (3.375, 6.575),
            (3.375, 6.610),
            (3.325, 6.610),
            (3.325, 6.575),
        ], srid=4326)
        
        DeliveryZone.objects.create(
            name='Ikeja Zone',
            restaurant=restaurants["Domino's Pizza Ikeja"],
            area=ikeja_zone,
            delivery_fee=500,
            min_order=3000,
            estimated_time=30,
        )
        
        self.stdout.write('✅ Created delivery zones')
        
        # ─────────────────────────────────────────────────────────
        # GEODJANGO: MultiPolygon for Lagos service area
        # Lagos has multiple disconnected areas (mainland + islands)
        # ─────────────────────────────────────────────────────────
        lagos_mainland = Polygon([
            (3.250, 6.450),
            (3.420, 6.450),
            (3.420, 6.640),
            (3.250, 6.640),
            (3.250, 6.450),
        ], srid=4326)
        
        lagos_island = Polygon([
            (3.380, 6.400),
            (3.520, 6.400),
            (3.520, 6.470),
            (3.380, 6.470),
            (3.380, 6.400),
        ], srid=4326)
        
        # MultiPolygon combines both areas
        lagos_boundary = MultiPolygon([lagos_mainland, lagos_island], srid=4326)
        
        ServiceArea.objects.create(
            name='Lagos Metropolitan Area',
            boundary=lagos_boundary,
            is_active=True,
        )
        
        self.stdout.write('✅ Created Lagos service area (MultiPolygon)')
        
        # Sample menu items
        mama_cass = restaurants['Mama Cass Restaurant']
        MenuItem.objects.bulk_create([
            MenuItem(restaurant=mama_cass, name='Jollof Rice + Chicken', price=2500, category='Rice Dishes', description='Party-style jollof rice with a full chicken quarter'),
            MenuItem(restaurant=mama_cass, name='Egusi Soup + Eba', price=2200, category='Soups', description='Rich egusi soup with stockfish and assorted meat, served with eba'),
            MenuItem(restaurant=mama_cass, name='Pounded Yam + Ofe Oha', price=2800, category='Soups', description='Smooth pounded yam with Oha leaf soup'),
            MenuItem(restaurant=mama_cass, name='Banga Soup + Starch', price=2400, category='Soups', description='Creamy banga soup with catfish and orishirishi'),
            MenuItem(restaurant=mama_cass, name='Moi Moi + Akara', price=1200, category='Sides', description='Steamed bean pudding with fried bean cakes'),
            MenuItem(restaurant=mama_cass, name='Chapman', price=800, category='Drinks', description='Nigerian cocktail with Fanta, Sprite, grenadine and cucumber'),
        ])
        
        suya_spot = restaurants['Suya Spot Surulere']
        MenuItem.objects.bulk_create([
            MenuItem(restaurant=suya_spot, name='Beef Suya (200g)', price=1500, category='Suya', description='Premium beef marinated in suya spice blend, grilled over open fire'),
            MenuItem(restaurant=suya_spot, name='Chicken Suya (300g)', price=1800, category='Suya', description='Juicy chicken pieces grilled to perfection with suya spice'),
            MenuItem(restaurant=suya_spot, name='Ram Suya (200g)', price=2000, category='Suya', description='Special cut ram meat, extra tender and flavorful'),
            MenuItem(restaurant=suya_spot, name='Gizzard Suya', price=1200, category='Suya', description='Crispy chicken gizzard suya'),
            MenuItem(restaurant=suya_spot, name='Zobo Drink', price=500, category='Drinks', description='Cold hibiscus drink with ginger and pineapple flavor'),
        ])
        
        self.stdout.write(f'\n{"="*50}')
        self.stdout.write('✅ Database seeded successfully!')
        self.stdout.write(f'{"="*50}\n')
        self.stdout.write('📍 Summary:')
        self.stdout.write(f'  • {Restaurant.objects.count()} restaurants (PointField locations in Lagos)')
        self.stdout.write(f'  • {DeliveryZone.objects.count()} delivery zones (PolygonField areas)')
        self.stdout.write(f'  • {ServiceArea.objects.count()} service area (MultiPolygonField)')
        self.stdout.write(f'  • {MenuItem.objects.count()} menu items')
        self.stdout.write('\n🗺️  Test the API:')
        self.stdout.write('  Nearby search: GET /api/restaurants/nearby/?lat=6.44&lng=3.42&radius=5')
        self.stdout.write('  Zone check:    GET /api/zones/check/?lat=6.43&lng=3.42')
        self.stdout.write('  All zones:     GET /api/zones/')