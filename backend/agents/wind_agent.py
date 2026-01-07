import random
import math
import logging

from typing import Dict, Any
from ..constants import WIND_UPDATE_TICKER_INTERVAL, WIND_EFFECT_FACTOR

logger = logging.getLogger(__name__)


class WindAgent:
    def __init__(self):
        self.direction = random.uniform(0, 360)  # 0=North, 90=East, 180=South, 270=West
        self.speed = random.uniform(2, 8)

        logger.info(
            f"Initial Wind: direction {self.direction:.1f}°, speed {self.speed:.1f} m/s"
        )

        self.tick_count = 0

    def update(self) -> Dict[str, Any]:
        """Update wind."""
        self.tick_count += 1

        if self.tick_count % WIND_UPDATE_TICKER_INTERVAL == 0:
            old_direction = self.direction
            old_speed = self.speed

            self.direction = (self.direction + random.uniform(-5, 5)) % 360

            self.speed += random.uniform(-0.5, 0.5)
            self.speed = max(0, min(self.speed, 15))  # Keep between 0-15 m/s

            logger.info(
                f"Wind changed: direction {old_direction:.1f}° -> {self.direction:.1f}°, speed {old_speed:.1f} m/s -> {self.speed:.1f} m/s"
            )
        return self.get_current_conditions()

    def get_current_conditions(self) -> Dict[str, Any]:
        """Get current wind conditions."""
        return {"direction": round(self.direction, 1), "speed": round(self.speed, 1)}

    @staticmethod
    def calculate_wind_effect(
        wind_conditions: Dict[str, Any],
        shot_direction: float,
        shot_distance: float,
    ) -> Dict[str, float]:
        """Calculate wind effect on a golf shot."""
        wind_direction = wind_conditions["direction"]
        wind_speed = wind_conditions["speed"]

        # Calculate relative angle between wind and shot
        relative_angle = (wind_direction - math.degrees(shot_direction)) % 360
        if relative_angle > 180:
            relative_angle -= 360
        relative_angle_rad = math.radians(relative_angle)

        wind_factor = wind_speed * WIND_EFFECT_FACTOR

        distance_change = shot_distance * wind_factor * math.cos(relative_angle_rad)
        lateral_deviation = shot_distance * wind_factor * math.sin(relative_angle_rad)

        return {
            "distance_change": round(distance_change, 1),
            "lateral_deviation": round(lateral_deviation, 1),
        }

    def get_wind_effect_on_shot(
        self, shot_direction: float, shot_distance: float
    ) -> Dict[str, float]:
        """Calculate wind effect on a golf shot using current conditions."""
        return WindAgent.calculate_wind_effect(
            self.get_current_conditions(), shot_direction, shot_distance
        )
