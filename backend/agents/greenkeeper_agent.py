import math
import random
import logging
from typing import Dict, Any, Optional, List

from ..constants import (
    WALKING_SPEED,
    FLAG_PLACEMENT_DURATION_TICKS,
    HOLE_SERVICE_INTERVAL_TICKS,
)
from ..utils.calculations import Calculations

logger = logging.getLogger(__name__)


class GreenkeeperAgent:
    """Rule-based greenkeeper agent that moves flag positions on all holes."""

    def __init__(
        self,
        id: int,
        num_holes: int,
        holes_data: Dict[int, Dict[str, Any]],
        navigation_paths: Dict = None,
        water: List = None,
        bridges: List = None,
    ):
        self.id = id
        self.position = {"x": 100, "y": -520}
        self.state = "idle"  # idle, walking_to_hole, placing_flag
        self.current_hole = None
        self.target_position = None
        self.flag_placement_timer = 0
        self.num_holes = num_holes
        self.holes_data = holes_data
        self.navigation_paths = navigation_paths if navigation_paths else {}
        self.water = water if water else []
        self.bridges = bridges if bridges else []

        # Path following state
        self.current_path = []
        self.current_waypoint_index = 0
        self.last_hole = None
        self.final_flag_selected = False

        # Initialize timers for each hole - all holes need service at start
        self.hole_timers = {
            hole_num: HOLE_SERVICE_INTERVAL_TICKS
            for hole_num in range(1, num_holes + 1)
        }
        self.holes_needing_service = set(range(1, num_holes + 1))

    def _select_closest_hole_needing_service(self) -> Optional[int]:
        """Rule: Select the closest hole that needs service."""
        if not self.holes_needing_service:
            return None

        closest_hole = None
        min_distance = float("inf")

        for hole_num in self.holes_needing_service:
            green_center = self._get_green_center(hole_num)
            distance = Calculations.get_distance(self.position, green_center)

            if distance < min_distance:
                min_distance = distance
                closest_hole = hole_num

        return closest_hole

    def _get_green_center(self, hole_num: int) -> Dict[str, float]:
        """Get the center position of a hole's green."""
        green = self.holes_data[hole_num]["green"]
        center_x = sum(p["x"] for p in green) / len(green)
        center_y = sum(p["y"] for p in green) / len(green)
        return {"x": center_x, "y": center_y}

    def _select_new_flag_position(self, hole_data: Dict[str, Any]) -> Dict[str, float]:
        """Rule: Select a random position on the green for the new flag."""
        green = hole_data["green"]

        min_x = min(p["x"] for p in green)
        max_x = max(p["x"] for p in green)
        min_y = min(p["y"] for p in green)
        max_y = max(p["y"] for p in green)

        max_attempts = 250
        for _ in range(max_attempts):
            candidate = {
                "x": random.uniform(min_x, max_x),
                "y": random.uniform(min_y, max_y),
            }

            if Calculations.point_in_polygon(candidate, green):
                return candidate

        avg_x = sum(p["x"] for p in green) / len(green)
        avg_y = sum(p["y"] for p in green) / len(green)
        return {"x": avg_x, "y": avg_y}

    def _get_navigation_path(
        self, from_hole: Optional[int], to_hole: int
    ) -> List[Dict[str, float]]:
        """Get pre-computed navigation path between holes (green center to green center)."""
        if from_hole and (from_hole, to_hole) in self.navigation_paths:
            path = self.navigation_paths[(from_hole, to_hole)]
            logger.info(
                f"Greenkeeper: Using pre-computed path from hole {from_hole} to {to_hole} with {len(path)} waypoints"
            )
            return path.copy()

        target_green_center = self._get_green_center(to_hole)
        return [target_green_center]

    def start_next_task(self):
        """Rule: If idle and there are holes needing service, select closest one."""
        if self.state == "idle":
            next_hole = self._select_closest_hole_needing_service()
            if next_hole is not None:
                self.current_hole = next_hole

                self.current_path = self._get_navigation_path(self.last_hole, next_hole)
                self.current_waypoint_index = 0

                logger.info(
                    f"Greenkeeper: Starting journey from hole {self.last_hole} to hole {next_hole}"
                )
                logger.info(
                    f"Greenkeeper: Current position: ({self.position['x']:.1f}, {self.position['y']:.1f})"
                )
                logger.info(f"Greenkeeper: Path has {len(self.current_path)} waypoints")
                if self.current_path:
                    logger.info(
                        f"Greenkeeper: First waypoint: ({self.current_path[0]['x']:.1f}, {self.current_path[0]['y']:.1f}) - {self.current_path[0].get('type', 'unknown')}"
                    )

                if self.current_path:
                    first_waypoint = self.current_path[0]
                    distance_to_first = Calculations.get_distance(
                        self.position, first_waypoint
                    )

                    if distance_to_first < 1.0 and len(self.current_path) > 1:
                        self.current_waypoint_index = 1
                        logger.info(
                            f"Greenkeeper: Already at first waypoint, starting from waypoint 1"
                        )

                self.target_position = self.current_path[
                    self.current_waypoint_index
                ].copy()
                self.state = "walking_to_hole"
                self.holes_needing_service.discard(next_hole)
                self.final_flag_selected = False

    def update(self) -> Dict[str, Any]:
        """Update greenkeeper state based on rules."""
        result = {
            "id": self.id,
            "state": self.state,
            "position": self.position.copy(),
            "current_hole": self.current_hole,
            "flag_changed": False,
            "new_flag_position": None,
        }

        for hole_num in range(1, self.num_holes + 1):
            if hole_num != self.current_hole:
                self.hole_timers[hole_num] += 1

                if self.hole_timers[hole_num] >= HOLE_SERVICE_INTERVAL_TICKS:
                    self.holes_needing_service.add(hole_num)

        if self.state == "idle":
            self.start_next_task()

        if self.state == "walking_to_green_center" and self.target_position:
            distance = Calculations.get_distance(self.position, self.target_position)

            if distance < 1.0:
                self.position = self.target_position.copy()
                self.state = "idle"
                self.final_flag_selected = False
                logger.info(
                    f"Greenkeeper: Reached green center of hole {self.current_hole}"
                )
            else:
                direction = Calculations.get_direction(
                    self.position, self.target_position
                )
                move_distance = min(WALKING_SPEED, distance)
                self.position["x"] += direction["x"] * move_distance
                self.position["y"] += direction["y"] * move_distance

        if self.state == "walking_to_hole" and self.target_position:
            distance = Calculations.get_distance(self.position, self.target_position)

            if distance < 1.0:
                self.position = self.target_position.copy()

                if self.current_waypoint_index < len(self.current_path) - 1:
                    self.current_waypoint_index += 1
                    self.target_position = self.current_path[
                        self.current_waypoint_index
                    ].copy()
                    waypoint = self.current_path[self.current_waypoint_index]
                    logger.info(
                        f"Greenkeeper: Reached waypoint {self.current_waypoint_index}/{len(self.current_path)} - Next: ({waypoint['x']:.1f}, {waypoint['y']:.1f}) - {waypoint.get('type', 'unknown')}"
                    )
                elif not self.final_flag_selected:
                    new_flag_position = self._select_new_flag_position(
                        self.holes_data[self.current_hole]
                    )

                    self.final_flag_selected = True

                    flag_distance = Calculations.get_distance(
                        self.position, new_flag_position
                    )
                    if flag_distance < 1.0:
                        self.target_position = new_flag_position
                        self.state = "placing_flag"
                        self.flag_placement_timer = 0
                        logger.info(
                            f"Greenkeeper: Starting flag placement on hole {self.current_hole}"
                        )
                    else:
                        self.target_position = new_flag_position
                        logger.info(
                            f"Greenkeeper: Walking to new flag position on hole {self.current_hole} ({flag_distance:.1f}m away)"
                        )
                else:
                    self.state = "placing_flag"
                    self.flag_placement_timer = 0
                    logger.info(
                        f"Greenkeeper: Reached final flag position, starting placement on hole {self.current_hole}"
                    )
            else:
                direction = Calculations.get_direction(
                    self.position, self.target_position
                )
                move_distance = min(WALKING_SPEED, distance)
                self.position["x"] += move_distance * math.cos(direction)
                self.position["y"] += move_distance * math.sin(direction)

        elif self.state == "placing_flag":
            self.flag_placement_timer += 1

            if self.flag_placement_timer >= FLAG_PLACEMENT_DURATION_TICKS:
                result["flag_changed"] = True
                result["new_flag_position"] = self.target_position.copy()
                result["hole_number"] = self.current_hole

                self.hole_timers[self.current_hole] = 0
                self.holes_needing_service.discard(self.current_hole)

                self.last_hole = self.current_hole

                green_center = self._get_green_center(self.current_hole)
                distance_to_center = Calculations.get_distance(
                    self.position, green_center
                )

                if distance_to_center > 1.0:
                    self.target_position = green_center
                    self.state = "walking_to_green_center"
                    logger.info(
                        f"Greenkeeper: Walking to green center of hole {self.current_hole}"
                    )
                else:
                    self.state = "idle"
                    self.current_hole = None
                    self.target_position = None
                    self.flag_placement_timer = 0
                    self.current_path = []
                    self.current_waypoint_index = 0

        result["state"] = self.state
        result["position"] = self.position.copy()

        # Handle walking to green center after placing flag
        if self.state == "walking_to_green_center" and self.target_position:
            distance = Calculations.get_distance(self.position, self.target_position)

            if distance < 1.0:
                self.position = self.target_position.copy()
                self.state = "idle"
                self.current_hole = None
                self.target_position = None
                self.flag_placement_timer = 0
                self.current_path = []
                self.current_waypoint_index = 0
                logger.info(f"Greenkeeper: Reached green center, now idle")
            else:
                direction = Calculations.get_direction(
                    self.position, self.target_position
                )
                move_distance = min(WALKING_SPEED, distance)
                self.position["x"] += move_distance * math.cos(direction)
                self.position["y"] += move_distance * math.sin(direction)

        return result

    def get_state(self) -> Dict[str, Any]:
        """Get current greenkeeper state."""
        return {
            "id": self.id,
            "position": self.position,
            "state": self.state,
            "current_hole": self.current_hole,
            "holes_needing_service": len(self.holes_needing_service),
        }
