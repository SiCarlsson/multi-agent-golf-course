import json
import logging
from pathlib import Path

from ..simulation.player_group import PlayerGroup

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Core simulation engine to manage the golf course simulation."""

    def __init__(self):
        self.holes = {}
        self.player_groups = []
        self.greenkeeper = None
        self.tick_count = 0

        self._load_all_holes()
        self.num_holes = len(self.holes)

    def _load_all_holes(self):
        """Load all hole data into the simulation engine."""
        course_data_dir = Path(__file__).parent.parent / "data" / "course"

        hole_files = sorted(course_data_dir.glob("hole_*.json"))

        for hole_file in hole_files:
            hole_num = int(hole_file.stem.split("_")[1])

            with open(hole_file, "r") as f:
                self.holes[hole_num] = json.load(f)

    def tick(self):
        """Process one simulation step for all active groups."""
        self.tick_count += 1
        flag_update = None

        if self.greenkeeper:
            greenkeeper_result = self.greenkeeper.update()

            if greenkeeper_result["flag_changed"]:
                hole_num = greenkeeper_result["hole_number"]
                new_flag_pos = greenkeeper_result["new_flag_position"]
                self.holes[hole_num]["flag"] = new_flag_pos
                flag_update = {"hole": hole_num, "position": new_flag_pos}
                logger.info(
                    f"Greenkeeper changed flag on hole {hole_num} to position {new_flag_pos}"
                )

        for group in self.player_groups:
            if not group.is_complete:
                hole_data = self.holes[group.current_hole_number]

                if not group.all_shots_taken_this_round():
                    group.set_current_turn_index(hole_data)
                    player = group.players[group.current_turn_index]

                    if (
                        not player.is_complete
                        and group.current_turn_index in group.players_need_to_shoot
                    ):
                        # Check if it's safe to shoot (greenkeeper not in landing zone)
                        greenkeeper_pos = self.greenkeeper.position if self.greenkeeper else None
                        can_shoot = player.can_take_shot(hole_data, greenkeeper_pos)
                        
                        if can_shoot:
                            shot_result = player.take_shot(hole_data)
                            group.players_need_to_shoot.discard(group.current_turn_index)
                            logger.info(
                                f"Player {player.id} took shot {shot_result['stroke_number']}"
                            )
                        else:
                            logger.info(
                                f"Player {player.id} waiting - greenkeeper too close to landing zone"
                            )
                    elif player.is_complete:
                        group.players_need_to_shoot.discard(group.current_turn_index)
                        logger.info(
                            f"Player {player.id} has completed hole {group.current_hole_number}."
                        )

                    if all(p.is_complete for p in group.players):
                        self._advance_group_to_next_hole(group)

                elif not group.are_all_players_at_ball():
                    group.walk_all_players_to_balls()
                    logger.info(f"Group {group.group_id} players walking to balls")

                else:
                    group.mark_all_players_need_to_shoot()

        return self.get_state(flag_update)

    def _advance_group_to_next_hole(self, group: PlayerGroup):
        """Advance the group to the next hole or mark as complete."""
        if group.current_hole_number < self.num_holes:
            old_hole = group.current_hole_number
            group.current_hole_number += 1
            logger.info(
                f"Group {group.group_id} completed hole {old_hole}, advancing to hole {group.current_hole_number}."
            )
            for player in group.players:
                player.is_complete = False
                tee_pos = self.get_tee_position(
                    self.holes[group.current_hole_number]["tees"][0]
                )
                player.player_position = tee_pos
                player.ball_position = tee_pos.copy()
                player.state = "idle"
                player.strokes = 0
            group.mark_all_players_need_to_shoot()
        else:
            group.is_complete = True
            logger.info(f"Group {group.group_id} has completed the course.")

    def get_tee_position(self, tee_box: dict) -> dict:
        """Get the tee position for the hole."""
        avg_x = sum(p["x"] for p in tee_box) / len(tee_box)
        avg_y = sum(p["y"] for p in tee_box) / len(tee_box)
        return {"x": avg_x, "y": avg_y}

    def get_state(self, flag_update=None):
        """Get current simulation state."""
        state = {
            "tick": self.tick_count,
            "groups": [
                {
                    "current_hole": group.current_hole_number,
                    "players": [player.get_state() for player in group.players],
                }
                for group in self.player_groups
            ],
        }

        if self.greenkeeper:
            state["greenkeeper"] = self.greenkeeper.get_state()

        if flag_update:
            state["flag_update"] = flag_update

        return state
