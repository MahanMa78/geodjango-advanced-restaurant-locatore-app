"""
The Nominatim service is highly sensitive regarding the User-Agent format;
it immediately blocks requests if the standard format—which 
requires a valid email address and a specific text structure—is not
followed or if the string "example.com" is detected.
Additionally, if requests are sent in rapid succession without any delay,
Nominatim’s filtering policy identifies the activity as scraping.
"""


import logging
import requests

logger = logging.getLogger(__name__)

class NominatimGeocodingService:
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

    @classmethod
    def reverse_geocode(cls, lat: float, lng: float) -> dict:
        """
        Converting geographic coordinates to a Persian/structured text address
        """
        params = {
            "lat": lat,
            "lon": lng,
            "format": "jsonv2",
            "accept-language": "fa,en", 
            "addressdetails": 1,
        }
        
        
        headers = {
            "User-Agent": "MahanRestaurantLocatorApp/1.0 (mahan78ir@gmail.com)",
            "Accept": "application/json",
            "Referer": "http://localhost:5173"
        }

        try:
            response = requests.get(cls.NOMINATIM_URL, params=params, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()

            address = data.get("address", {})

            city = address.get("city") or address.get("town") or address.get("county") or "unknown"
            neighbourhood = address.get("neighbourhood") or address.get("suburb") or address.get("quarter") or ""
            road = address.get("road") or address.get("pedestrian") or ""

            display_name = data.get("display_name", "")
            short_address_parts = [p for p in [city, neighbourhood, road] if p]
            short_address = "، ".join(short_address_parts) if short_address_parts else "Address unknown"

            return {
                "success": True,
                "full_address": display_name,
                "short_address": short_address,
                "city": city,
                "neighbourhood": neighbourhood,
                "road": road,
                "raw_address": address
            }

        except requests.RequestException as e:
            logger.error(f"Geocoding Error: {e}")
            return {
                "success": False,
                "error": "Error retrieving address from the map service.",
                "short_address": "Address unknown"
            }