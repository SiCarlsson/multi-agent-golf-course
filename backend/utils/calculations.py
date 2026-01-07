import math


class Calculations:
    @staticmethod
    def get_distance(pos1: dict, pos2: dict) -> float:
        dx = pos2["x"] - pos1["x"]
        dy = pos2["y"] - pos1["y"]
        return math.sqrt(dx * dx + dy * dy)

    @staticmethod
    def get_direction(from_pos, to_pos) -> float:
        """Return angle in radians."""
        dx = to_pos["x"] - from_pos["x"]
        dy = to_pos["y"] - from_pos["y"]
        return math.atan2(dy, dx)

    @staticmethod
    def point_in_polygon(point, polygon: list) -> bool:
        """Check if a point is inside a polygon using ray casting algorithm."""
        if isinstance(point, dict):
            x, y = point["x"], point["y"]
        else:
            x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]["x"], polygon[0]["y"]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]["x"], polygon[i % n]["y"]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    @staticmethod
    def get_polygon_center(polygon: list) -> dict:
        """Get the center point of a polygon."""
        if not polygon:
            return {"x": 0, "y": 0}

        x_sum = sum(p["x"] for p in polygon)
        y_sum = sum(p["y"] for p in polygon)
        n = len(polygon)

        return {"x": x_sum / n, "y": y_sum / n}

    @staticmethod
    def line_segment_intersects_polygon(start: dict, end: dict, polygon: list) -> dict:
        """Find the first intersection point where a line enters a polygon."""

        def line_intersection(p1, p2, p3, p4):
            """Find intersection point of two lines (p1-p2) and (p3-p4)."""
            x1, y1 = p1["x"], p1["y"]
            x2, y2 = p2["x"], p2["y"]
            x3, y3 = p3["x"], p3["y"]
            x4, y4 = p4["x"], p4["y"]

            denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if abs(denom) < 1e-10:
                return None

            t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
            u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

            if 0 <= t <= 1 and 0 <= u <= 1:
                return {"x": x1 + t * (x2 - x1), "y": y1 + t * (y2 - y1)}
            return None

        if Calculations.point_in_polygon(start, polygon):
            return start

        closest_intersection = None
        min_distance = float("inf")

        n = len(polygon)
        for i in range(n):
            p1 = polygon[i]
            p2 = polygon[(i + 1) % n]

            intersection = line_intersection(start, end, p1, p2)
            if intersection:
                distance = Calculations.get_distance(start, intersection)
                if distance < min_distance:
                    min_distance = distance
                    closest_intersection = intersection

        return closest_intersection
