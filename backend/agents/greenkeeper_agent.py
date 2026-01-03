import math
import random
from typing import Dict, Any, Optional

from ..constants import (
    WALKING_SPEED,
    FLAG_PLACEMENT_DURATION_TICKS,
    HOLE_SERVICE_INTERVAL_TICKS,
    GREENKEEPER_IDLE_DISTANCE_METERS,
)
from ..utils.calculations import Calculations


class GreenkeeperAgent:
    """Rule-based greenkeeper agent that moves flag positions on all holes."""

    def __init__(self, id: int, num_holes: int, holes_data: Dict[int, Dict[str, Any]]):
        self.id = id
        self.position = {"x": 0, "y": 0}
        self.state = "idle"  # idle, walking_to_hole, placing_flag, walking_to_idle
        self.current_hole = None
        self.target_position = None
        self.flag_placement_timer = 0
        self.num_holes = num_holes
        self.holes_data = holes_data

        # Initialize timers for each hole (all start needing service)
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
            hole_flag = self.holes_data[hole_num]["flag"]
            distance = Calculations.get_distance(self.position, hole_flag)

            if distance < min_distance:
                min_distance = distance
                closest_hole = hole_num

        return closest_hole

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

    def _is_too_close_to_features(
        self, position: Dict[str, float], polygons: list
    ) -> bool:
        """Helper: Check if position is inside or within GREENKEEPER_IDLE_DISTANCE_METERS of any polygon."""
        for polygon in polygons:
            if Calculations.point_in_polygon(position, polygon):
                return True

            for angle in [0, math.pi / 2, math.pi, 3 * math.pi / 2]:
                check_point = {
                    "x": position["x"] + GREENKEEPER_IDLE_DISTANCE_METERS * math.cos(angle),
                    "y": position["y"] + GREENKEEPER_IDLE_DISTANCE_METERS * math.sin(angle),
                }
                if Calculations.point_in_polygon(check_point, polygon):
                    return True
        return False

    def _calculate_idle_position(self, hole_data: Dict[str, Any]) -> Dict[str, float]:
        """Rule: Calculate position 20m away from fairway, bunkers, and tees to avoid interfering with play."""
        fairway = hole_data["fairway"]
        bunkers = hole_data.get("bunkers", [])
        tees = hole_data.get("tees", [])

        # Handle fairway being either a single polygon or list of polygons
        fairways = [fairway] if fairway and isinstance(fairway[0], dict) else fairway

        for _ in range(250):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(
                GREENKEEPER_IDLE_DISTANCE_METERS, GREENKEEPER_IDLE_DISTANCE_METERS * 2
            )

            candidate = {
                "x": self.position["x"] + distance * math.cos(angle),
                "y": self.position["y"] + distance * math.sin(angle),
            }

            if self._is_too_close_to_features(candidate, fairways):
                continue
            if self._is_too_close_to_features(candidate, bunkers):
                continue
            if self._is_too_close_to_features(candidate, tees):
                continue

            return candidate

        # Fallback: fixed position at x:20, y:0
        return {"x": 20, "y": 0}

    def start_next_task(self):
        """Rule: If idle and there are holes needing service, select closest one."""
        if self.state == "idle":
            next_hole = self._select_closest_hole_needing_service()
            if next_hole is not None:
                self.current_hole = next_hole
                self.target_position = self._select_new_flag_position(
                    self.holes_data[next_hole]
                )
                self.state = "walking_to_hole"
                # Remove from needing service while being serviced
                self.holes_needing_service.discard(next_hole)

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

        if self.state == "walking_to_hole" and self.target_position:
            distance = Calculations.get_distance(self.position, self.target_position)

            if distance < 1.0:  # Reached target
                self.position = self.target_position.copy()
                self.state = "placing_flag"
                self.flag_placement_timer = 0
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

                idle_position = self._calculate_idle_position(
                    self.holes_data[self.current_hole]
                )
                self.target_position = idle_position
                self.state = "walking_to_idle"
                self.flag_placement_timer = 0

        elif self.state == "walking_to_idle" and self.target_position:
            distance = Calculations.get_distance(self.position, self.target_position)

            if distance < GREENKEEPER_IDLE_DISTANCE_METERS:
                self.position = self.target_position.copy()
                self.state = "idle"
                self.current_hole = None
                self.target_position = None
            else:
                direction = Calculations.get_direction(
                    self.position, self.target_position
                )
                move_distance = min(WALKING_SPEED, distance)
                self.position["x"] += move_distance * math.cos(direction)
                self.position["y"] += move_distance * math.sin(direction)

        result["state"] = self.state
        result["position"] = self.position.copy()

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
