import React, { useEffect, useState } from "react";
import type { Hole, Ball } from "./models";
import { SimulationPresenter } from "./presenters/SimulationPresenter";
import { CanvasRenderer } from "./views/CanvasRender";

const initialHole: Hole = {
  fairway: [
    { x: 50, y: 50 },
    { x: 200, y: 50 },
    { x: 400, y: 150 },
    { x: 500, y: 200 },
  ],
  green: [
    { x: 480, y: 180 },
    { x: 520, y: 180 },
    { x: 520, y: 220 },
    { x: 480, y: 220 },
  ],
  tee: { x: 50, y: 50 },
  flag: { x: 500, y: 200 },
};

const initialBall: Ball = { x: 50, y: 50 };

function App() {
  const [hole, setHole] = useState<Hole>(initialHole);
  const [ball, setBall] = useState<Ball>(initialBall);

  const presenter = React.useMemo(() => new SimulationPresenter(hole, ball), []);

  useEffect(() => {
    presenter.subscribe(({ hole, ball }) => {
      setHole(hole);
      setBall({ ...ball });
    });

    const interval = setInterval(() => presenter.tick(), 50); // 20 FPS
    return () => clearInterval(interval);
  }, [presenter]);

  return <CanvasRenderer hole={hole} ball={ball} />;
}

export default App;
