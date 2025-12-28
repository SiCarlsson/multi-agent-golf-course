import math
from typing import Dict, Any, List

from ..constants import (
    BASE_MAX_DISTANCE,
    CLUB_MULTIPLIERS,
    HOLE_COMPLETION_DISTANCE,
    LIE_MULTIPLIERS_DISTANCE,
    LIE_MULTIPLIERS_UTILITY,
    NUMBER_OF_POWER_STEPS_TO_VALIDATE,
    NUMBER_OF_DIRECTION_STEPS_TO_VALIDATE,
)
from ..utils.calculations import Calculations


class ShotUtility:
    """Utility-based decision making for golf shots."""

    @staticmethod
    def select_best_shot(
        ball_position: Dict[str, float],
        current_lie: str,
        player_strength: float,
        hole_data: Dict[str, Any],
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
        )

        best_shot = None
        best_utility = float("-inf")

        for shot in shot_options:
            utility = ShotUtility._calculate_shot_utility(shot, hole_data)
            shot["utility"] = utility

            if utility > best_utility:
                best_utility = utility
                best_shot = shot

        return best_shot

    @staticmethod
    def _generate_shot_options(
        ball_position: Dict[str, float],
        current_lie: str,
        player_strength: float,
        distance_to_flag: float,
        direction_to_flag: float,
        hole_data: Dict[str, Any],
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
                        ball_position, power, direction
                    )
                    landing_lie = ShotUtility.determine_lie(landing_pos, hole_data)

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
        shot: Dict[str, Any], hole_data: Dict[str, Any]
    ) -> float:
        """Calculate utility value for a shot option."""
        flag = hole_data["flag"]
        landing_pos = shot["landing_position"]
        landing_lie = shot["landing_lie"]

        distance_to_hole = Calculations.get_distance(landing_pos, flag)
        distance_utility = -distance_to_hole

        lie_adjustment = LIE_MULTIPLIERS_UTILITY.get(landing_lie, 1.0)

        total_utility = distance_utility * lie_adjustment

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

        lie_multiplier = LIE_MULTIPLIERS_DISTANCE.get(current_lie, 1.0)
        final_distance = strength_adjusted * lie_multiplier

        return max(final_distance, HOLE_COMPLETION_DISTANCE)

    @staticmethod
    def _calculate_landing_position(
        ball_position: Dict[str, float], power: float, direction: float
    ) -> Dict[str, float]:
        """Calculate where the ball will land based on shot power and direction."""
        new_x = ball_position["x"] + power * math.cos(direction)
        new_y = ball_position["y"] + power * math.sin(direction)

        return {"x": new_x, "y": new_y}

    @staticmethod
    def determine_lie(position: Dict[str, float], hole_data: Dict[str, Any]) -> str:
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

        #TODO: Add water check

        return "rough"
