import json
import logging
import random

from pathlib import Path

from ..agents.player_agent import PlayerAgent
from ..utils.pathfinding import PathFinder
from ..utils.calculations import Calculations
from ..simulation.player_group import PlayerGroup
from ..constants import MIN_DISTANCE_FROM_TEE_TO_SPAWN_NEW_GROUP


logger = logging.getLogger(__name__)


class SimulationEngine:
    """Core simulation engine to manage the golf course simulation."""

    def __init__(self):
        self.holes = {}
        self.player_groups = []
        self.greenkeeper = None
        self.wind_agent = None
        self.tick_count = 0
        self.water = []
        self.bridges = []
        self.greenkeeper_paths = {}

        # Dynamic group spawning
        self.next_group_id = 1
        self.next_player_id = 1

        self._load_all_holes()
        self._load_course_features()
        self._compute_greenkeeper_paths()
        self.num_holes = len(self.holes)

    def _load_all_holes(self):
        """Load all hole data into the simulation engine."""
        course_data_dir = Path(__file__).parent.parent / "data" / "course"

        hole_files = sorted(course_data_dir.glob("hole_*.json"))

        for hole_file in hole_files:
            hole_num = int(hole_file.stem.split("_")[1])

            with open(hole_file, "r") as f:
                self.holes[hole_num] = json.load(f)

    def _load_course_features(self):
        """Load course-wide features like water and bridges."""
        course_data_dir = Path(__file__).parent.parent / "data" / "course"

        # Load water
        water_file = course_data_dir / "water.json"
        if water_file.exists():
            with open(water_file, "r") as f:
                water_data = json.load(f)
                self.water = water_data.get("water", [])

        # Load bridges
        bridges_file = course_data_dir / "bridges.json"
        if bridges_file.exists():
            with open(bridges_file, "r") as f:
                bridges_data = json.load(f)
                self.bridges = bridges_data.get("bridges", [])

    def _compute_greenkeeper_paths(self):
        """Pre-compute shortest water-avoiding paths between all holes."""
        if not self.holes:
            return

        cache_file = (
            Path(__file__).parent.parent / "data" / "navigation_paths_cache.json"
        )

        if cache_file.exists():
            try:
                logger.info("Loading greenkeeper paths from cache...")
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                    self.greenkeeper_paths = {
                        tuple(map(int, k.split(","))): v for k, v in cache_data.items()
                    }
                logger.info(f"Loaded {len(self.greenkeeper_paths)} paths from cache")
                return
            except Exception as e:
                logger.warning(f"Failed to load path cache: {e}. Recomputing...")

        logger.info("Computing greenkeeper paths between all holes...")
        pathfinder = PathFinder(self.water, self.bridges, self.holes)
        self.greenkeeper_paths = pathfinder.compute_all_paths(self.holes)
        logger.info(
            f"Computed {len(self.greenkeeper_paths)} paths for greenkeeper navigation"
        )

        try:
            cache_data = {
                f"{k[0]},{k[1]}": v for k, v in self.greenkeeper_paths.items()
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)
            logger.info(f"Saved paths to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save path cache: {e}")

    def tick(self):
        """Process one simulation step for all active groups."""
        self.tick_count += 1
        flag_update = None

        if self.can_spawn_new_group():
            self.spawn_new_group()

        # Update wind conditions
        if self.wind_agent:
            self.wind_agent.update()

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
                logger.debug(
                    f"[Tick {self.tick_count}] Processing Group {group.group_id} on hole {group.current_hole_number}"
                )

                if all(p.is_complete for p in group.players):
                    logger.info(
                        f"[Tick {self.tick_count}] All players in Group {group.group_id} complete! Advancing to next hole."
                    )
                    completed_course = self._advance_group_to_next_hole(group)
                    if completed_course:
                        self.player_groups.remove(group)
                        logger.info(
                            f"Group {group.group_id} removed from course after completing all holes"
                        )
                    continue

                if not group.all_shots_taken_this_round():
                    logger.debug(
                        f"[Tick {self.tick_count}] Group {group.group_id}: Not all shots taken. "
                        f"Players need to shoot: {group.players_need_to_shoot}"
                    )
                    group.set_current_turn_index(hole_data)
                    player = group.players[group.current_turn_index]
                    logger.debug(
                        f"[Tick {self.tick_count}] Group {group.group_id}: Current turn - Player {player.id} "
                        f"(is_complete: {player.is_complete}, state: {player.state}, "
                        f"ball_pos: ({player.ball_position['x']:.2f}, {player.ball_position['y']:.2f}))"
                    )

                    if (
                        not player.is_complete
                        and group.current_turn_index in group.players_need_to_shoot
                    ):
                        greenkeeper_pos = self.greenkeeper.position
                        wind_conditions = self.wind_agent.get_current_conditions()

                        other_group_positions = (
                            self._get_other_group_positions_on_same_hole(group, player)
                        )

                        flag_distance = Calculations.get_distance(
                            player.ball_position, hole_data["flag"]
                        )
                        logger.debug(
                            f"[Tick {self.tick_count}] Player {player.id} in Group {group.group_id}: "
                            f"Distance to flag: {flag_distance:.2f}m, "
                            f"At player position: ({player.player_position['x']:.2f}, {player.player_position['y']:.2f}), "
                            f"Ball at: ({player.ball_position['x']:.2f}, {player.ball_position['y']:.2f})"
                        )

                        can_shoot = player.can_take_shot(
                            hole_data,
                            greenkeeper_pos,
                            wind_conditions,
                            other_group_positions,
                            self.water,
                        )

                        if can_shoot:
                            logger.info(
                                f"[Tick {self.tick_count}] Player {player.id} (Group {group.group_id}) taking shot. "
                                f"Distance to flag: {flag_distance:.2f}m, Strokes: {player.strokes}"
                            )
                            shot_result = player.take_shot(
                                hole_data, wind_conditions, self.water
                            )
                            group.players_need_to_shoot.discard(
                                group.current_turn_index
                            )
                            logger.info(
                                f"[Tick {self.tick_count}] Player {player.id} completed shot {shot_result['stroke_number']}. "
                                f"New distance: {shot_result['distance_to_flag']:.2f}m, is_complete: {shot_result['is_complete']}"
                            )
                        else:
                            logger.info(
                                f"[Tick {self.tick_count}] Player {player.id} (Group {group.group_id}) waiting - "
                                f"group or greenkeeper in landing zone"
                            )
                    elif player.is_complete:
                        group.players_need_to_shoot.discard(group.current_turn_index)
                        logger.info(
                            f"[Tick {self.tick_count}] Player {player.id} (Group {group.group_id}) has completed hole {group.current_hole_number}. "
                            f"Removing from players_need_to_shoot."
                        )
                    else:
                        logger.warning(
                            f"[Tick {self.tick_count}] Player {player.id} (Group {group.group_id}): "
                            f"Not in players_need_to_shoot but also not complete! "
                            f"is_complete: {player.is_complete}, current_turn_index: {group.current_turn_index}, "
                            f"players_need_to_shoot: {group.players_need_to_shoot}"
                        )

                    completion_status = [p.is_complete for p in group.players]
                    logger.debug(
                        f"[Tick {self.tick_count}] Group {group.group_id} completion status: {completion_status}"
                    )

                elif not group.are_all_players_at_ball():
                    for i, player in enumerate(group.players):
                        if not player.is_complete:
                            dist_to_ball = Calculations.get_distance(
                                player.player_position, player.ball_position
                            )
                            logger.debug(
                                f"[Tick {self.tick_count}] Group {group.group_id}, Player {player.id}: "
                                f"Walking to ball. Distance remaining: {dist_to_ball:.2f}m"
                            )
                    group.walk_all_players_to_balls()
                    logger.info(
                        f"[Tick {self.tick_count}] Group {group.group_id} players walking to balls"
                    )

                else:
                    incomplete_count = sum(
                        1 for p in group.players if not p.is_complete
                    )
                    if incomplete_count == 0:
                        logger.warning(
                            f"[Tick {self.tick_count}] Group {group.group_id}: All shots taken, players at ball, "
                            f"but all players complete. This should have been caught earlier!"
                        )
                    logger.debug(
                        f"[Tick {self.tick_count}] Group {group.group_id}: All players at ball. "
                        f"Marking all players to shoot. Current players_need_to_shoot: {group.players_need_to_shoot}, "
                        f"Incomplete players: {incomplete_count}"
                    )
                    group.mark_all_players_need_to_shoot()
                    logger.debug(
                        f"[Tick {self.tick_count}] Group {group.group_id}: After marking, players_need_to_shoot: {group.players_need_to_shoot}"
                    )

        return self.get_state(flag_update)

    def _get_other_group_positions_on_same_hole(
        self, current_group: PlayerGroup, current_player
    ) -> list[dict]:
        """Get ball positions of players from other groups on the same hole that are ahead."""
        positions = []
        hole_data = self.holes[current_group.current_hole_number]
        flag_position = hole_data["flag"]

        current_distance_to_flag = Calculations.get_distance(
            current_player.ball_position, flag_position
        )

        for other_group in self.player_groups:
            if other_group.group_id == current_group.group_id:
                continue

            if other_group.current_hole_number != current_group.current_hole_number:
                continue

            for other_player in other_group.players:
                if not other_player.is_complete:
                    other_distance_to_flag = Calculations.get_distance(
                        other_player.ball_position, flag_position
                    )
                    if other_distance_to_flag < current_distance_to_flag:
                        positions.append(other_player.ball_position)

        return positions

    def _advance_group_to_next_hole(self, group: PlayerGroup) -> bool:
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
            return False
        else:
            group.is_complete = True
            logger.info(
                f"Group {group.group_id} has completed the course (all 18 holes)."
            )
            return True

    def can_spawn_new_group(self) -> bool:
        """Check if conditions allow spawning a new group on hole 1."""
        groups_on_hole_1 = [g for g in self.player_groups if g.current_hole_number == 1]

        if not groups_on_hole_1:
            return True

        if len(groups_on_hole_1) >= 2:
            logger.debug(
                f"Cannot spawn: {len(groups_on_hole_1)} groups already on hole 1 (max 1 playing + 1 waiting)"
            )
            return False

        tee_position = self.get_tee_position(self.holes[1]["tees"][0])

        for group in groups_on_hole_1:
            for player in group.players:
                distance_from_tee = Calculations.get_distance(
                    player.ball_position, tee_position
                )
                if distance_from_tee < MIN_DISTANCE_FROM_TEE_TO_SPAWN_NEW_GROUP:
                    logger.debug(
                        f"Cannot spawn: Player {player.id} in Group {group.group_id} "
                        f"only {distance_from_tee:.2f}m from tee (need {MIN_DISTANCE_FROM_TEE_TO_SPAWN_NEW_GROUP}m)"
                    )
                    return False

        return True

    def spawn_new_group(self):
        """Spawn a new player group on hole 1 with random players."""
        num_players = random.randint(2, 4)
        players = []

        for i in range(num_players):
            accuracy = random.uniform(0.7, 0.9)
            strength = random.uniform(0.75, 0.95)

            player = PlayerAgent(
                id=self.next_player_id, accuracy=accuracy, strength=strength
            )
            players.append(player)
            logger.info(
                f"Created Player {self.next_player_id} with accuracy={accuracy:.2f}, strength={strength:.2f}"
            )
            self.next_player_id += 1

        new_group = PlayerGroup(
            id=self.next_group_id,
            players=players,
            starting_hole=1,
            tee_time=self.tick_count,
        )

        tee_box = self.holes[1]["tees"][4]
        tee_position = self.get_tee_position(tee_box)

        for player in new_group.players:
            player.player_position = tee_position.copy()
            player.ball_position = tee_position.copy()

        self.player_groups.append(new_group)

        self.next_group_id += 1

        logger.info(
            f"[Tick {self.tick_count}] Spawned Group {new_group.group_id} on hole 1 "
            f"with {num_players} players"
        )

        return new_group

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

        state["greenkeeper"] = self.greenkeeper.get_state()
        state["wind"] = self.wind_agent.get_current_conditions()

        if flag_update:
            state["flag_update"] = flag_update

        return state
