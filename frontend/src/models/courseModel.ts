import type { Point } from ".";

export interface Hole {
  fairway: Point[];
  green: Point[];
  tees: Point[][];
  flag: Point;
  bunkers?: Point[][];
  water?: Point[][];
}