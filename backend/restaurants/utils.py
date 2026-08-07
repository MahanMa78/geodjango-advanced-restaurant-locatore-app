import json
import pygeohash as geohash
from django.core.cache import cache

def get_spatial_cache(lat, lng, radius, category=None, precision=5):
    """
    Generating a lookup key based on the region's Geohash.
    precision=5 corresponds to a spatial area of ​​approximately 4.9 x 4.9 km.
    """
    gh = geohash.encode(lat, lng, precision=precision)
    cache_key = f"nearby_cache:{gh}:r{radius}:c{category or 'all'}"
    
    cached_data = cache.get(cache_key)
    if cached_data:
        try:
            return json.loads(cached_data), True
        except Exception:
            return cache_key, False
        
    return cache_key, False

def set_spatial_cache(cache_key, data, timeout=300):
    """Saving data in Redis with a 5-minute expiration (300 seconds)"""
    if isinstance(cache_key, str):
        cache.set(cache_key, json.dumps(data), timeout=timeout)