import type { Hole, Ball } from "../models";

type Subscriber = (state: { hole: Hole; ball: Ball }) => void;

export class SimulationPresenter {
  private hole: Hole;
  private ball: Ball;
  private subscribers: Subscriber[] = [];

  constructor(hole: Hole, ball: Ball) {
    this.hole = hole;
    this.ball = ball;
  }

  subscribe(fn: Subscriber) {
    this.subscribers.push(fn);
  }

  private notify() {
    this.subscribers.forEach((fn) => fn({ hole: this.hole, ball: this.ball }));
  }

  tick() {
    // Simple demo: move ball diagonally
    this.ball.x += 1;
    this.ball.y += 0.5;
    this.notify();
  }
}
