# backend/restaurants/pricing_service.py
from datetime import datetime, time
import math
from .models import PricingConfig

class DynamicPricingService:
    """
    Smart service for dynamic courier delivery cost calculation based on OSRM distance and time slots.
    """

    @staticmethod
    def calculate_delivery_fee(distance_km: float, current_datetime: datetime = None) -> dict:
        """
        Calculate the final delivery fee and provide a detailed breakdown (Breakdown)
        """
        if current_datetime is None:
            current_datetime = datetime.now()

        config = PricingConfig.get_active_config()

        # 1. Distance calculation
        base_fee = config.base_fee
        distance_component = int(distance_km * config.per_km_rate)
        subtotal = base_fee + distance_component

        # 2. Check peak hours
        current_time = current_datetime.time()
        
        lunch_start = time(12, 0)
        lunch_end = time(15, 30)
        dinner_start = time(19, 0)
        dinner_end = time(22, 30)

        peak_multiplier = float(1.0)
        surge_reasons = []

        if lunch_start <= current_time <= lunch_end:
            peak_multiplier = float(config.lunch_peak_multiplier)
            surge_reasons.append("Lunch Peak Hour 🔥")
        elif dinner_start <= current_time <= dinner_end:
            peak_multiplier = float(config.dinner_peak_multiplier)
            surge_reasons.append("Dinner Peak Hour 🔥")

        # 3. Check special conditions (rain/traffic)
        condition_multiplier = float(config.condition_multiplier)
        if condition_multiplier > 1.0:
            surge_reasons.append("Special Weather or Traffic Conditions 🌧️")

        # 4. Apply all multipliers to the base price
        combined_multiplier = peak_multiplier * condition_multiplier
        calculated_raw_fee = int(subtotal * combined_multiplier)

        # 5. Round to the nearest 500 Tomans (for price aesthetics in the invoice)
        rounded_fee = math.ceil(calculated_raw_fee / 500) * 500

        # 6. Applying price floors and ceilings (Clamping)
        final_fee = max(config.min_fee, min(rounded_fee, config.max_fee))

        return {
            "final_fee": final_fee,
            "base_fee": base_fee,
            "distance_component": distance_component,
            "distance_km": round(distance_km, 2),
            "is_peak_hour": peak_multiplier > 1.0,
            "peak_multiplier": peak_multiplier,
            "condition_multiplier": condition_multiplier,
            "combined_multiplier": round(combined_multiplier, 2),
            "surge_reasons": surge_reasons,
            "is_clamped_min": final_fee == config.min_fee and calculated_raw_fee < config.min_fee,
            "is_clamped_max": final_fee == config.max_fee and calculated_raw_fee > config.max_fee,
        }