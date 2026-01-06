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
