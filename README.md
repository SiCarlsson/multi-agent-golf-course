# Multi-Agent Golf Simulation

This is a course project for Artificial Intelligence and Applications (ID1214) at the Royal Institute of Technology (KTH).

---

### Frontend (React + TypeScript)

- **React + TypeScript** – component-based, type-safe
- **TailwindCSS** – HUD, scoreboards, buttons, and panels
- **Canvas 2D API** – draws fairways, greens, sand, water, players, balls, and weather

### Backend (Python)

- **Python**
- **FastAPI** – REST API
  - **Communication**: JSON via HTTP polling (WebSocket support planned)
- **Multi-agent simulation** (in development):
  - Player agents
  - Greenkeeper agents
  - Weather system

---

## **Getting Started**

### Backend Setup

1. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

2. Install Python dependencies:

   ```bash
   pip install -r backend/requirements.txt
   ```

3. Start the backend server:
   ```bash
   uvicorn backend.main:app --reload
   ```
   The backend will run on `http://localhost:8000`

### Frontend Setup

1. Install Node dependencies:

   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend will run on `http://localhost:5173`

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
