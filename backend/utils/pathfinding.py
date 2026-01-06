import heapq
import logging

from typing import Dict, List, Tuple, Optional

from .calculations import Calculations

logger = logging.getLogger(__name__)


class PathFinder:
    """A* pathfinding system for navigating around water hazards."""

    def __init__(
        self,
        water: List[List[Dict]],
        bridges: List[List[Dict]],
        holes: List[Dict] = None,
    ):
        self.water = water
        self.bridges = bridges
        self.holes = holes or []
        self.waypoints = []
        self.graph = {}

    def _is_point_in_water(self, point: Dict[str, float]) -> bool:
        """Check if a point is inside any water hazard (excluding bridges)."""
        for water_polygon in self.water:
            if Calculations.point_in_polygon(point, water_polygon):
                for bridge in self.bridges:
                    if Calculations.point_in_polygon(point, bridge):
                        return False
                return True
        return False

    def _path_crosses_water(
        self, start: Dict[str, float], end: Dict[str, float]
    ) -> bool:
        """Check if a straight line path crosses water without using a bridge."""
        if not self.water:
            return False

        dx = end["x"] - start["x"]
        dy = end["y"] - start["y"]
        path_length = (dx * dx + dy * dy) ** 0.5

        num_samples = max(20, int(path_length / 5))

        for i in range(num_samples + 1):
            t = i / num_samples
            sample_x = start["x"] + t * (end["x"] - start["x"])
            sample_y = start["y"] + t * (end["y"] - start["y"])
            sample_point = {"x": sample_x, "y": sample_y}

            in_water = any(
                Calculations.point_in_polygon(sample_point, w) for w in self.water
            )

            if in_water:
                if self.bridges:
                    on_bridge = any(
                        Calculations.point_in_polygon(sample_point, b)
                        for b in self.bridges
                    )
                    if not on_bridge:
                        return True
                else:
                    return True

        return False

    def _generate_waypoints(self, holes: Dict[int, Dict]) -> List[Dict[str, float]]:
        """Generate waypoints from hole centers, bridges, and safe zones around water."""
        waypoints = []

        for hole_num in sorted(holes.keys()):
            green = holes[hole_num].get("green", [])
            if green:
                center_x = sum(p["x"] for p in green) / len(green)
                center_y = sum(p["y"] for p in green) / len(green)
                waypoints.append(
                    {"x": center_x, "y": center_y, "type": "hole", "hole_num": hole_num}
                )

                if len(green) >= 4:
                    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        best_point = None
                        best_score = -float("inf")
                        for point in green:
                            score = (point["x"] - center_x) * dx + (
                                point["y"] - center_y
                            ) * dy
                            if score > best_score:
                                best_score = score
                                best_point = point
                        if best_point:
                            waypoints.append(
                                {
                                    "x": best_point["x"],
                                    "y": best_point["y"],
                                    "type": "green_edge",
                                    "hole_num": hole_num,
                                }
                            )

        for bridge in self.bridges:
            center = Calculations.get_polygon_center(bridge)
            waypoints.append({"x": center["x"], "y": center["y"], "type": "bridge"})

            for point in bridge:
                waypoints.append(
                    {"x": point["x"], "y": point["y"], "type": "bridge_edge"}
                )

        offset_distance = 30
        for water in self.water:
            if not water:
                continue

            min_x = min(p["x"] for p in water)
            max_x = max(p["x"] for p in water)
            min_y = min(p["y"] for p in water)
            max_y = max(p["y"] for p in water)

            candidates = [
                {"x": min_x - offset_distance, "y": min_y - offset_distance},
                {"x": max_x + offset_distance, "y": min_y - offset_distance},
                {"x": max_x + offset_distance, "y": max_y + offset_distance},
                {"x": min_x - offset_distance, "y": max_y + offset_distance},
                {"x": (min_x + max_x) / 2, "y": min_y - offset_distance},
                {"x": (min_x + max_x) / 2, "y": max_y + offset_distance},
                {"x": min_x - offset_distance, "y": (min_y + max_y) / 2},
                {"x": max_x + offset_distance, "y": (min_y + max_y) / 2},
            ]

            for candidate in candidates:
                if not self._is_point_in_water(candidate):
                    waypoints.append({**candidate, "type": "water_edge"})

        return waypoints

    def _build_graph(self, waypoints: List[Dict[str, float]]):
        """Build a graph of valid paths between waypoints."""
        self.graph = {i: [] for i in range(len(waypoints))}

        for i in range(len(waypoints)):
            for j in range(i + 1, len(waypoints)):
                if not self._path_crosses_water(waypoints[i], waypoints[j]):
                    distance = Calculations.get_distance(waypoints[i], waypoints[j])
                    self.graph[i].append((j, distance))
                    self.graph[j].append((i, distance))

    def _astar(self, start_idx: int, goal_idx: int) -> Optional[List[int]]:
        """A* pathfinding algorithm to find shortest path between waypoints."""
        if start_idx == goal_idx:
            return [start_idx]

        open_set = [(0, 0, start_idx, [start_idx])]
        visited = set()

        while open_set:
            f_score, g_score, current, path = heapq.heappop(open_set)

            if current in visited:
                continue

            visited.add(current)

            if current == goal_idx:
                return path

            for neighbor, edge_cost in self.graph.get(current, []):
                if neighbor not in visited:
                    new_g = g_score + edge_cost
                    # Heuristic: straight-line distance to goal
                    h = Calculations.get_distance(
                        self.waypoints[neighbor], self.waypoints[goal_idx]
                    )
                    new_f = new_g + h
                    new_path = path + [neighbor]
                    heapq.heappush(open_set, (new_f, new_g, neighbor, new_path))

        return None  # No path found

    def compute_all_paths(
        self, holes: Dict[int, Dict]
    ) -> Dict[Tuple[int, int], List[Dict[str, float]]]:
        """Pre-compute shortest paths between all pairs of holes."""
        self.waypoints = self._generate_waypoints(holes)
        self._build_graph(self.waypoints)

        hole_to_waypoint = {}
        for i, wp in enumerate(self.waypoints):
            if wp.get("type") == "hole":
                hole_to_waypoint[wp["hole_num"]] = i

        paths = {}
        hole_nums = sorted(holes.keys())

        for i, hole_a in enumerate(hole_nums):
            for hole_b in hole_nums[i + 1 :]:
                start_idx = hole_to_waypoint[hole_a]
                goal_idx = hole_to_waypoint[hole_b]

                if not self._path_crosses_water(
                    self.waypoints[start_idx], self.waypoints[goal_idx]
                ):
                    paths[(hole_a, hole_b)] = [
                        self.waypoints[start_idx],
                        self.waypoints[goal_idx],
                    ]
                    paths[(hole_b, hole_a)] = [
                        self.waypoints[goal_idx],
                        self.waypoints[start_idx],
                    ]
                else:
                    waypoint_path = self._astar(start_idx, goal_idx)
                    if waypoint_path:
                        path_coords = [self.waypoints[idx] for idx in waypoint_path]
                        paths[(hole_a, hole_b)] = path_coords
                        paths[(hole_b, hole_a)] = list(reversed(path_coords))
                    else:
                        logger.warning(
                            f"No water-avoiding path found between holes {hole_a} and {hole_b} - using direct path (may cross water)"
                        )
                        paths[(hole_a, hole_b)] = [
                            self.waypoints[start_idx],
                            self.waypoints[goal_idx],
                        ]
                        paths[(hole_b, hole_a)] = [
                            self.waypoints[goal_idx],
                            self.waypoints[start_idx],
                        ]

        return paths
