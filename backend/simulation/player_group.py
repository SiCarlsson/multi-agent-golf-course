import logging
from ..agents.player_agent import PlayerAgent
from ..utils.calculations import Calculations
from ..constants import SHOT_TAKING_DISTANCE

logger = logging.getLogger(__name__)


class PlayerGroup:
    def __init__(
        self, id: int, players: list[PlayerAgent], starting_hole: int, tee_time: int
    ):
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
        """Set the index of the player farthest from the pin who still needs to shoot this round."""
        pin_position = hole_data["flag"]

        next_player_index = 0
        max_distance = float("-inf")

        logger.debug(
            f"Group {self.group_id}: Determining current turn index. "
            f"Pin at ({pin_position['x']:.2f}, {pin_position['y']:.2f}), "
            f"players_need_to_shoot: {self.players_need_to_shoot}"
        )

        players_eligible_to_shoot = []
        for i, player in enumerate(self.players):
            if not player.is_complete and i in self.players_need_to_shoot:
                distance_to_pin = Calculations.get_distance(
                    player.ball_position, pin_position
                )
                players_eligible_to_shoot.append((i, distance_to_pin))
                logger.debug(
                    f"Group {self.group_id}, Player {player.id} (index {i}): "
                    f"distance to pin = {distance_to_pin:.2f}m, eligible to shoot"
                )

                if distance_to_pin > max_distance:
                    max_distance = distance_to_pin
                    next_player_index = i
            elif not player.is_complete:
                logger.debug(
                    f"Group {self.group_id}, Player {player.id} (index {i}): "
                    f"not complete but not in players_need_to_shoot (already shot this round)"
                )

        if not players_eligible_to_shoot:
            logger.warning(
                f"Group {self.group_id}: set_current_turn_index called but no players eligible! "
                f"players_need_to_shoot: {self.players_need_to_shoot}. Defaulting to index 0."
            )
            self.current_turn_index = 0
        else:
            self.current_turn_index = next_player_index
            logger.debug(
                f"Group {self.group_id}: Set current turn to index {next_player_index} "
                f"(Player {self.players[next_player_index].id}, max distance: {max_distance:.2f}m)"
            )

    def are_all_players_at_ball(self) -> bool:
        """Check if all players have finished walking to their balls."""
        all_at_ball = True
        for player in self.players:
            if player.is_complete:
                logger.debug(
                    f"Group {self.group_id}, Player {player.id}: completed, skipping"
                )
                continue
            distance = Calculations.get_distance(
                player.player_position, player.ball_position
            )
            logger.debug(
                f"Group {self.group_id}, Player {player.id}: distance to ball = {distance:.2f}m "
                f"(threshold: {SHOT_TAKING_DISTANCE}m)"
            )
            if distance >= SHOT_TAKING_DISTANCE:
                all_at_ball = False
        
        logger.debug(f"Group {self.group_id}: are_all_players_at_ball = {all_at_ball}")
        return all_at_ball

    def walk_all_players_to_balls(self):
        """Move all players one step towards their balls."""
        for player in self.players:
            if not player.is_complete:
                player.walk_to_ball()

    def mark_all_players_need_to_shoot(self):
        """Mark all incomplete players as needing to shoot this round."""
        before = self.players_need_to_shoot.copy()
        self.players_need_to_shoot = {
            i for i, player in enumerate(self.players) if not player.is_complete
        }
        logger.debug(
            f"Group {self.group_id} mark_all_players_need_to_shoot: "
            f"before={before}, after={self.players_need_to_shoot}. "
            f"Player completion status: {[(i, p.is_complete) for i, p in enumerate(self.players)]}"
        )

    def all_shots_taken_this_round(self) -> bool:
        """Check if all players who need to shoot have taken their shots."""
        return len(self.players_need_to_shoot) == 0
