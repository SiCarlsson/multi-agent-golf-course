import type { Point } from ".";

export interface Greenkeeper {
  id: number;
  currentTask: 'break' | 'placing_flag' | 'maintaining' | 'waiting';
  position?: Point;
  assignedHole?: number;
}