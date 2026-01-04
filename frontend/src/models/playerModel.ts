import type { Point } from "./index";

export interface Player {
  id: number;
  ball: Ball;
  score: number;
  position: Point;
  currentHole: number;
}

export interface Ball {
  position: Point;
}