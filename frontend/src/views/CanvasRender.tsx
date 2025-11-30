import React, { useRef, useEffect } from "react";
import type { Hole, Ball } from "../models";

interface Props {
  hole: Hole;
  ball: Ball;
}

export const CanvasRenderer: React.FC<Props> = ({ hole, ball }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

    // Draw fairway
    ctx.fillStyle = "#a2d149";
    ctx.beginPath();
    hole.fairway.forEach((p, i) =>
      i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)
    );
    ctx.closePath();
    ctx.fill();

    // Draw green
    ctx.fillStyle = "#34a853";
    ctx.beginPath();
    hole.green.forEach((p, i) =>
      i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y)
    );
    ctx.closePath();
    ctx.fill();

    // Draw ball
    ctx.fillStyle = "red";
    ctx.beginPath();
    ctx.arc(ball.x, ball.y, 5, 0, Math.PI * 2);
    ctx.fill();

    // Draw flag
    ctx.fillStyle = "yellow";
    ctx.beginPath();
    ctx.arc(hole.flag.x, hole.flag.y, 5, 0, Math.PI * 2);
    ctx.fill();
  }, [hole, ball]);

  return <canvas ref={canvasRef} width={800} height={400} />;
};
