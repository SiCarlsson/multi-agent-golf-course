export interface Point {
  x: number;
  y: number;
}

export interface Hole {
  fairway: Point[];
  green: Point[];
  tee: Point;
  flag: Point;
}

export interface Ball {
  x: number;
  y: number;
}