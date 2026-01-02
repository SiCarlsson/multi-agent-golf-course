# Multi-Agent Golf Simulation

This is a course project for Artificial Intelligence and Applications (ID1214) at the Royal Institute of Technology (KTH).

---

### Frontend (React + TypeScript)

- **React + TypeScript** – component-based, type-safe
- **Node.js** with **Vite** – fast build tooling and development server
- **TailwindCSS** – HUD, scoreboards, buttons, and panels
- **HTML5 Canvas** – draws fairways, greens, sand, water, players, balls, and weather

### Backend (Python)

- **Python**
- **FastAPI** – WebSocket API
  - **Communication**: Real-time updates via WebSocket connections
- **Multi-agent simulation** (in development):
  - Player agents
  - Greenkeeper agents
  - Weather system

---

## **Getting Started**

### Quick Start with Docker (Recommended)

The easiest way to run the entire application:

```bash
make docker-up
```

The application will be available at:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`

**Docker Commands:**

```bash
make docker-up         # Start containers
make docker-down       # Stop containers
make docker-rebuild    # Rebuild without cache
```

### Quick Start (Local Development)

Once dependencies are installed, run both servers simultaneously:

```bash
make dev
```

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
