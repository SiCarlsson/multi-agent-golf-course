# Multi-Agent Golf Simulation

This is a course project for Artificial Intelligence and Applications (ID1214) at the Royal Institute of Technology (KTH).

---

### Frontend (React + TypeScript)
- **React + TypeScript** – component-based, type-safe
- **TailwindCSS** – HUD, scoreboards, buttons, and panels
- **Canvas 2D API** – draws fairways, greens, sand, water, players, balls, and weather

### Backend (Python)
- **Python**
- **FastAPI** – REST and WebSocket API
  - **Communication**: JSON via WebSocket
- **Multi-agent simulation**:
  - Players
  - Wind agent
  - Weather agent (per hole)
  - Greenkeepers

---

## **Frontend Architecture / MVP Structure**

- **Model**
  - Holes, fairway/green/sand/water polygons
  - Agent positions
  - Weather and wind
- **Presenter**
  - Handles backend updates
  - Tick-based simulation
- **View**
  - `CanvasRenderer` draws polygons and agents
  - HUD and panels rendered with Tailwind