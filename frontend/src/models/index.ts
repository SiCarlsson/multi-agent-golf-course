import type { Hole } from "./holeModel";
import type { Greenkeeper } from "./greenKeeperModel";
import type { Player } from "./playerModel";
import type { Weather } from "./weatherModel";

export interface Point {
  x: number;
  y: number;
}

export interface GameState {
  players: Player[];
  greenkeepers: Greenkeeper[];
  weather: Weather;
}

export interface CourseData {
  holes: Hole[];
}