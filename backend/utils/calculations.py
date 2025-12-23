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