"""
Management command: python manage.py seed_data

Seeds DERIVED spatial data (delivery zones, service-area boundary) and 
sample menu items for whatever restaurants already exist in the database 
(typically imported via `import_restaurants_online`).

USAGE EXAMPLES:
  1. Default run (seeds missing zones/menus for all DB restaurants):
     python manage.py seed_data

  2. Seed with a custom delivery radius (e.g., 2.0 km):
     python manage.py seed_data --radius-km 2.0

  3. Filter by city and force-rebuild existing zones/menus:
     python manage.py seed_data --city "Qazvin" --reseed

DOCKER USAGE:
  docker-compose exec web python manage.py seed_data --city "Qazvin" --reseed
  docker-compose exec web python manage.py seed_data --radius-km 2.0

GEODJANGO CONCEPTS DEMONSTRATED:
  1. Deriving Polygon delivery zones from real Point locations
  2. Accurate metric buffering via CRS transformation (SRID 4326 <-> 3857)
  3. Building a MultiPolygon ServiceArea using Convex Hull geometry
  4. Idempotent seeding (safe to re-run without creating duplicate data)
"""   

from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import MultiPoint, MultiPolygon, Polygon
from restaurants.models import Restaurant, MenuItem
from zones.models import DeliveryZone, ServiceArea

"""
Web Mercator — good enough for short-distance buffering in meters.
(Not accurate for polar regions or very large areas, but fine for
city-scale delivery zones.)
"""
METRIC_SRID = 3857
GEOGRAPHIC_SRID = 4326
"""
Generic fallback menu, used when a restaurant's category doesn't match
a more specific template below. Keyed by Category.name so it's trivial
to extend as import_restaurants_online starts capturing more OSM `cuisine`
tags in the future.
"""
MENU_TEMPLATES = {
    "Pizza": [
        ("Margherita Pizza", 450000, "Main", "Classic tomato, mozzarella and basil."),
        ("Pepperoni Pizza", 520000, "Main", "Loaded with pepperoni and extra cheese."),
        ("Garlic Bread", 150000, "Side", "Toasted with garlic butter."),
        ("Soft Drink", 80000, "Drinks", "Chilled can."),
    ],
    "Iranian": [
        ("Chelo Kabab Koobideh", 350000, "Main", "Two skewers of minced beef, saffron rice, and grilled tomato."),
        ("Ghormeh Sabzi", 280000, "Main", "Traditional Persian herb stew with lamb, kidney beans, and dried lime."),
        ("Zereshk Polo ba Morgh", 290000, "Main", "Saffron rice with barberries served with tender chicken."),
        ("Kashk-e Bademjan", 150000, "Starter", "Sautéed eggplant with kashk, caramelized onions, and mint."),
        ("Doogh", 35000, "Drinks", "Traditional chilled mint yogurt drink."),
    ],
    "Italian": [
        ("Pizza Margherita", 280000, "Main", "Classic Neapolitan pizza with tomato sauce, mozzarella, and fresh basil."),
        ("Penne Carbonara", 310000, "Main", "Pasta with egg yolk, guanciale, pecorino cheese, and black pepper."),
        ("Lasagna Bolognese", 330000, "Main", "Layered pasta with rich meat ragù, béchamel, and parmesan."),
        ("Bruschetta al Pomodoro", 140000, "Starter", "Grilled garlic bread topped with fresh tomatoes, basil, and olive oil."),
        ("Tiramisu", 120000, "Dessert", "Classic Italian coffee-flavored dessert."),
    ],
    # Default template — used for the generic "Restaurant"/"Fast Food"/
    # "Cafe" categories that import_restaurants_online currently assigns.
    "__default__": [
        ("Chef's Special Combo", 550000, "Main", "House specialty, chef's choice."),
        ("Grilled Chicken Plate", 420000, "Main", "Served with rice and salad."),
        ("Fries", 120000, "Side", "Crispy golden fries."),
        ("Soft Drink", 80000, "Drinks", "Chilled can."),
    ],
}
 
 
class Command(BaseCommand):
    help = (
        "Seeds delivery zones, a service area, and sample menu items for "
        "restaurants already imported by import_restaurants_online. City-agnostic: "
        "derives every coordinate from the restaurants actually in the DB."
    )
 
    def add_arguments(self, parser):
        parser.add_argument(
            "--city",
            type=str,
            default=None,
            help=(
                "Restrict seeding to restaurants whose address contains this "
                "string (matches the --city value you used for import_restaurants_online). "
                "Omit to seed derived data for every restaurant in the DB."
            ),
        )
        parser.add_argument(
            "--radius-km",
            type=float,
            default=1.5,
            help="Delivery zone radius, in kilometers, around each restaurant (default: 1.5).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Optional cap on how many restaurants to seed (default: all matching restaurants).",
        )
        parser.add_argument(
            "--reseed",
            action="store_true",
            help="Delete and recreate zones/menus for the selected restaurants instead of skipping ones that already have data.",
        )
 
    def handle(self, *args, **options):
        city = options["city"]
        radius_km = options["radius_km"]
        limit = options["limit"]
        reseed = options["reseed"]
 
        restaurants = Restaurant.objects.select_related("category").all()
        if city:
            restaurants = restaurants.filter(address__icontains=city)
        if limit:
            restaurants = restaurants[:limit]
 
        if not restaurants.exists():
            raise CommandError(
                "No matching restaurants found. Run `import_restaurants_online` "
                "first" + (f" for city '{city}'." if city else ".")
            )
 
        restaurants = list(restaurants)
        label = city or f"{len(restaurants)} restaurant(s) in the database"
        self.stdout.write(f"🌍 Seeding derived data for {label}...\n")
 
        if reseed:
            self._clear_existing(restaurants)
 
        zones_created = self._seed_delivery_zones(restaurants, radius_km)
        self._seed_service_area(restaurants, city)
        menus_created = self._seed_menu_items(restaurants)
 
        self.stdout.write(f"\n{'=' * 50}")
        self.stdout.write(self.style.SUCCESS("✅ Done"))
        self.stdout.write(f"{'=' * 50}")
        self.stdout.write(f"  • {zones_created} delivery zone(s) created")
        self.stdout.write(f"  • {menus_created} restaurant(s) received menu items")
        self.stdout.write(f"  • {ServiceArea.objects.count()} service area(s) in total")
 
    # ------------------------------------------------------------------
    # Delivery zones
    # ------------------------------------------------------------------
    def _seed_delivery_zones(self, restaurants, radius_km):
        """
        Builds one circular delivery zone per restaurant, centered on its
        REAL location. Unlike a naive `location.x ± 0.015`, this reprojects
        into a metric CRS to buffer by an actual distance in meters, so the
        zone radius is correct regardless of the city's latitude.
        """
        created = 0
        for restaurant in restaurants:
            if not restaurant.location:
                continue
            # With --reseed, _clear_existing() already wiped old zones, so this
            # check simply guards default (non-reseed) runs against duplicates.
            if DeliveryZone.objects.filter(restaurant=restaurant).exists():
                continue
 
            zone_polygon = self._buffer_point_km(restaurant.location, radius_km)
 
            DeliveryZone.objects.update_or_create(
                restaurant=restaurant,
                defaults=dict(
                    name=f"{restaurant.name} Delivery Zone",
                    area=zone_polygon,
                    # Reuse the restaurant's own figures instead of
                    # re-hardcoding fee/minimum/time constants — they were
                    # already set sensibly at import time.
                    delivery_fee=restaurant.delivery_fee,
                    min_order=restaurant.minimum_order,
                    estimated_time=restaurant.delivery_time_min,
                ),
            )
            created += 1
 
        self.stdout.write(f"✅ Created/updated {created} delivery zone(s) (radius ≈ {radius_km} km)")
        return created
 
    def _buffer_point_km(self, point, radius_km) -> Polygon:
        """Buffer a Point by `radius_km` kilometers using a metric CRS, returning a Polygon in SRID 4326."""
        metric_point = point.clone()
        metric_point.transform(METRIC_SRID)
        buffered = metric_point.buffer(radius_km * 1000)  # meters
        buffered.srid = METRIC_SRID
        buffered.transform(GEOGRAPHIC_SRID)
        return buffered
 
    # ------------------------------------------------------------------
    # Service area
    # ------------------------------------------------------------------
    def _seed_service_area(self, restaurants, city):
        """
        Builds a ServiceArea boundary as the convex hull of every restaurant
        location, expanded by a small margin — instead of hand-drawn
        mainland/island polygons for one specific city. Works for any bbox.
        """
        points = MultiPoint([r.location for r in restaurants if r.location], srid=GEOGRAPHIC_SRID)
 
        hull = points.convex_hull
        # convex_hull of <3 points can degrade to a Point or LineString;
        # buffer it in metric space so we always end up with a Polygon.
        metric_hull = hull.clone()
        metric_hull.srid = GEOGRAPHIC_SRID
        metric_hull.transform(METRIC_SRID)
        margin_m = 500  # small buffer so the boundary comfortably contains every point
        boundary_metric = metric_hull.buffer(margin_m)
        boundary_metric.srid = METRIC_SRID
        boundary_metric.transform(GEOGRAPHIC_SRID)
 
        boundary = MultiPolygon([boundary_metric], srid=GEOGRAPHIC_SRID)
        name = f"{city} Service Area" if city else "Service Area"
 
        ServiceArea.objects.update_or_create(
            name=name,
            defaults=dict(boundary=boundary, is_active=True),
        )
        self.stdout.write(f"✅ Created/updated service area '{name}' (convex hull of {len(points)} restaurant locations)")
 
    # ------------------------------------------------------------------
    # Menu items
    # ------------------------------------------------------------------
    def _seed_menu_items(self, restaurants):
        """
        Adds a small sample menu to any restaurant that doesn't already have
        one. Template is picked by Category.name, falling back to a generic
        template — this is intentionally the extension point for when
        import_restaurants_online starts mapping OSM `cuisine` tags to more
        specific categories.
        """
        seeded = 0
        for restaurant in restaurants:
            if MenuItem.objects.filter(restaurant=restaurant).exists():
                continue  # idempotent: don't duplicate menus on re-run
 
            category_name = restaurant.category.name if restaurant.category else None
            template = MENU_TEMPLATES.get(category_name, MENU_TEMPLATES["__default__"])
 
            MenuItem.objects.bulk_create(
                [
                    MenuItem(
                        restaurant=restaurant,
                        name=name,
                        price=price,
                        category=item_category,
                        description=description,
                    )
                    for name, price, item_category, description in template
                ]
            )
            seeded += 1
 
        self.stdout.write(f"✅ Seeded menu items for {seeded} restaurant(s)")
        return seeded
 
    # ------------------------------------------------------------------
    def _clear_existing(self, restaurants):
        """Used with --reseed to force a clean rebuild for the selected restaurants only."""
        DeliveryZone.objects.filter(restaurant__in=restaurants).delete()
        MenuItem.objects.filter(restaurant__in=restaurants).delete()
        self.stdout.write("🧹 Cleared existing zones/menus for selected restaurants (--reseed)")
