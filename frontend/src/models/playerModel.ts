import type { Point } from "./index";

export interface Player {
  id: number;
  ball: Ball;
  score: number;
  position: Point;
  currentHole: number;
  startTime: string;
  stopTime?: string[];
  state: 'waiting for greenkeeper' | 'waiting for others' | 'queuing' | 'aiming' | 'swinging' | 'finished';
}

export interface Ball {
  position: Point;
}