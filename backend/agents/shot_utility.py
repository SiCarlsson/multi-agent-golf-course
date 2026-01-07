import math
import logging
from typing import Dict, Any, List

from .wind_agent import WindAgent
from ..constants import (
    BASE_MAX_DISTANCE,
    CLUB_MULTIPLIERS,
    HOLE_COMPLETION_DISTANCE,
    LIE_MULTIPLIERS_DISTANCE,
    LIE_MULTIPLIERS_UTILITY,
    NUMBER_OF_POWER_STEPS_TO_VALIDATE,
    NUMBER_OF_DIRECTION_STEPS_TO_VALIDATE,
    WRONG_HOLE_UTILITY_PENALTY,
)
from ..utils.calculations import Calculations

logger = logging.getLogger(__name__)


class ShotUtility:
    @staticmethod
    def select_best_shot(
        ball_position: Dict[str, float],
        current_lie: str,
        player_strength: float,
        hole_data: Dict[str, Any],
        wind_conditions: Dict[str, Any] = None,
        player_accuracy: float = 1.0,
        water: List[List[Dict[str, float]]] = None,
        current_hole_number: int = None,
        all_holes: Dict[int, Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        flag = hole_data["flag"]
        distance_to_flag = Calculations.get_distance(ball_position, flag)
        direction_to_flag = Calculations.get_direction(ball_position, flag)

        shot_options = ShotUtility._generate_shot_options(
            ball_position,
            current_lie,
            player_strength,
            distance_to_flag,
            direction_to_flag,
            hole_data,
            wind_conditions,
            player_accuracy,
            water,
        )

        best_shot = None
        best_utility = float("-inf")

        water_shots_rejected = 0
        total_shots = len(shot_options)

        for shot in shot_options:
            utility = ShotUtility._calculate_shot_utility(
                shot, hole_data, current_hole_number, all_holes
            )
            shot["utility"] = utility

            if shot["landing_lie"] == "water":
                water_shots_rejected += 1

            if utility > best_utility:
                best_utility = utility
                best_shot = shot

        if water_shots_rejected > 0:
            logger.info(
                f"Shot selection: Rejected {water_shots_rejected}/{total_shots} options due to water. "
                f"Selected: club={best_shot['club']}, lie={best_shot['landing_lie']}"
            )

        return best_shot

    @staticmethod
    def _generate_shot_options(
        ball_position: Dict[str, float],
        current_lie: str,
        player_strength: float,
        distance_to_flag: float,
        direction_to_flag: float,
        hole_data: Dict[str, Any],
        wind_conditions: Dict[str, Any] = None,
        player_accuracy: float = 1.0,
        water: List[List[Dict[str, float]]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate multiple shot options to evaluate."""
        options = []

        clubs_to_consider = ShotUtility._get_available_clubs(
            distance_to_flag, current_lie
        )

        for club in clubs_to_consider:
            max_distance = ShotUtility._get_club_max_distance(
                club, player_strength, current_lie
            )

            step = int(100 / NUMBER_OF_POWER_STEPS_TO_VALIDATE)
            for percentage in range(0, 101, step):
                power = max_distance * (percentage / 100)

                step = int(60 / NUMBER_OF_DIRECTION_STEPS_TO_VALIDATE)
                for degrees in range(-30, 31, step):
                    direction = direction_to_flag + math.radians(degrees)

                    landing_pos = ShotUtility._calculate_landing_position(
                        ball_position,
                        power,
                        direction,
                        wind_conditions,
                        player_accuracy,
                    )
                    landing_lie = ShotUtility.determine_lie(
                        landing_pos, hole_data, water
                    )

                    options.append(
                        {
                            "club": club,
                            "power": power,
                            "direction": direction,
                            "landing_position": landing_pos,
                            "landing_lie": landing_lie,
                        }
                    )

        return options

    @staticmethod
    def _calculate_shot_utility(
        shot: Dict[str, Any],
        hole_data: Dict[str, Any],
        current_hole_number: int = None,
        all_holes: Dict[int, Dict[str, Any]] = None,
    ) -> float:
        """Calculate utility value for a shot option."""
        flag = hole_data["flag"]
        landing_pos = shot["landing_position"]
        landing_lie = shot["landing_lie"]

        # Heavily penalize water shots
        if landing_lie == "water":
            logger.debug(
                f"WATER HAZARD: Rejected shot landing at ({landing_pos['x']:.2f}, {landing_pos['y']:.2f}) - would land in water"
            )
            return float("-inf")

        distance_to_hole = Calculations.get_distance(landing_pos, flag)
        distance_utility = -distance_to_hole

        lie_adjustment = LIE_MULTIPLIERS_UTILITY.get(landing_lie, 1.0)

        total_utility = distance_utility * lie_adjustment

        if current_hole_number and all_holes:
            for hole_num, hole in all_holes.items():
                if hole_num == current_hole_number:
                    continue

                if "fairway" in hole and Calculations.point_in_polygon(
                    landing_pos, hole["fairway"]
                ):
                    total_utility -= WRONG_HOLE_UTILITY_PENALTY
                    break

                if "green" in hole and Calculations.point_in_polygon(
                    landing_pos, hole["green"]
                ):
                    total_utility -= WRONG_HOLE_UTILITY_PENALTY
                    break

        return total_utility

    @staticmethod
    def _get_available_clubs(distance_to_flag: float, current_lie: str) -> List[str]:
        """Determine which clubs are appropriate for the distance and lie."""
        if current_lie == "green":
            return ["putter"]
        elif distance_to_flag < 50:
            return ["wedge", "putter"]
        elif distance_to_flag < 150:
            return ["wedge", "iron"]
        else:
            return ["driver", "iron"]

    @staticmethod
    def _get_club_max_distance(
        club: str, player_strength: float, current_lie: str
    ) -> float:
        """Get maximum distance for a club considering player strength and lie."""
        base_distance = BASE_MAX_DISTANCE * CLUB_MULTIPLIERS[club]

        strength_adjusted = base_distance * player_strength
        lie_multiplier = LIE_MULTIPLIERS_DISTANCE.get(current_lie)

        lie_multiplier = LIE_MULTIPLIERS_DISTANCE.get(current_lie, 1.0)
        final_distance = strength_adjusted * lie_multiplier

        return max(final_distance, HOLE_COMPLETION_DISTANCE)

    @staticmethod
    def _calculate_landing_position(
        ball_position: Dict[str, float],
        power: float,
        direction: float,
        wind_conditions: Dict[str, Any] = None,
        player_accuracy: float = 1.0,
    ) -> Dict[str, float]:
        """Calculate where the ball will land based on shot power, direction, and wind."""
        new_x = ball_position["x"] + power * math.cos(direction)
        new_y = ball_position["y"] + power * math.sin(direction)

        wind_effect = WindAgent.calculate_wind_effect(wind_conditions, direction, power)

        distance_change = wind_effect["distance_change"]
        lateral_deviation = wind_effect["lateral_deviation"]

        wind_compensation_error = 1.0 - player_accuracy

        effective_distance_change = distance_change * wind_compensation_error
        effective_lateral_deviation = lateral_deviation * wind_compensation_error

        new_x += effective_distance_change * math.cos(direction)
        new_y += effective_distance_change * math.sin(direction)
        new_x += effective_lateral_deviation * math.cos(direction + math.pi / 2)
        new_y += effective_lateral_deviation * math.sin(direction + math.pi / 2)

        return {"x": new_x, "y": new_y}

    @staticmethod
    def determine_lie(
        position: Dict[str, float],
        hole_data: Dict[str, Any],
        water: List[List[Dict[str, float]]] = None,
    ) -> str:
        """Determine what type of lie the ball is in."""
        if "green" in hole_data and Calculations.point_in_polygon(
            position, hole_data["green"]
        ):
            return "green"

        if "bunkers" in hole_data:
            for bunker in hole_data["bunkers"]:
                if Calculations.point_in_polygon(position, bunker):
                    return "bunker"

        if "fairway" in hole_data and Calculations.point_in_polygon(
            position, hole_data["fairway"]
        ):
            return "fairway"

        if water:
            for water_polygon in water:
                if Calculations.point_in_polygon(position, water_polygon):
                    return "water"

        return "rough"
