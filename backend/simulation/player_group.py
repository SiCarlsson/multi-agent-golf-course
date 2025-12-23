from ..agents.player_agent import PlayerAgent
from ..utils.calculations import Calculations


class PlayerGroup:
    def __init__(self, id: int, players: list[PlayerAgent], starting_hole: int, tee_time: int):
        self.group_id = id
        self.players = players
        self.current_hole_number = starting_hole
        self.tee_time = tee_time
        self.current_turn_index = 0
        self.is_complete = False

    def get_current_turn_index(self) -> int:
        """Get the index of the player whose turn it is."""
        return self.current_turn_index

    def set_current_turn_index(self, hole_data: dict):
        """Set the index of the player farthest from the pin (they play next)."""
        pin_position = hole_data["flag"]

        next_player_index = 0
        max_distance = float("-inf")

        for i, player in enumerate(self.players):
            if not player.is_complete:
                distance_to_pin = Calculations.get_distance(player.position, pin_position)

                if distance_to_pin > max_distance:
                    max_distance = distance_to_pin
                    next_player_index = i

        self.current_turn_index = next_player_index
