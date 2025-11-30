export interface Point {
  x: number;
  y: number;
}

export interface Hole {
  fairway: Point[];
  green: Point[];
  tees: Point[][];
  flag: Point;
  bunkers?: Point[][];
  water?: Point[][];
}

export interface Ball {
  x: number;
  y: number;
}