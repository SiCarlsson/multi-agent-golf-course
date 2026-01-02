from ..agents.player_agent import PlayerAgent
from ..utils.calculations import Calculations
from ..constants import SHOT_TAKING_DISTANCE


class PlayerGroup:
    def __init__(self, id: int, players: list[PlayerAgent], starting_hole: int, tee_time: int):
        self.group_id = id
        self.players = players
        self.current_hole_number = starting_hole
        self.tee_time = tee_time
        self.current_turn_index = 0
        self.is_complete = False
        self.players_need_to_shoot = set()

        self.mark_all_players_need_to_shoot()

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
                distance_to_pin = Calculations.get_distance(player.ball_position, pin_position)

                if distance_to_pin > max_distance:
                    max_distance = distance_to_pin
                    next_player_index = i

        self.current_turn_index = next_player_index
    
    def are_all_players_at_ball(self) -> bool:
        """Check if all players have finished walking to their balls."""
        for player in self.players:
            if player.is_complete:
                continue
            distance = Calculations.get_distance(player.player_position, player.ball_position)
            if distance >= SHOT_TAKING_DISTANCE:
                return False
        return True
    
    def walk_all_players_to_balls(self):
        """Move all players one step towards their balls."""
        for player in self.players:
            if not player.is_complete:
                player.walk_to_ball()

    def mark_all_players_need_to_shoot(self):
        """Mark all incomplete players as needing to shoot this round."""
        self.players_need_to_shoot = {
            i for i, player in enumerate(self.players) if not player.is_complete
        }
    
    def all_shots_taken_this_round(self) -> bool:
        """Check if all players who need to shoot have taken their shots."""
        return len(self.players_need_to_shoot) == 0

