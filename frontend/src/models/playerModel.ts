import type { Point } from "./index";

export interface Player {
  id: number;
  ball: Ball;
  score: number;
  position: Point;
  currentHole: number;
  startTime: string;
  stopTime?: string[];
}

export interface Ball {
  position: Point;
}