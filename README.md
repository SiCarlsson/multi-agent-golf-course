# Multi-Agent Golf Simulation

This is the course project for Artificial Intelligence and Applications (ID1214) at the Royal Institute of Technology (KTH).

---

### Project description

A multi-agent golf course simulation featuring autonomous AI agents navigating and playing on an 18-hole golf course. The simulation uses utility-based decision making for players, rule-based pathfinding for the greenkeeper, and a stochastic model (random walk) for wind.

---

### Frontend (React + TypeScript)

- **React + TypeScript** – frontend framework, handles golf course animations
- **Node.js** with **Vite** – frontend server
- **TailwindCSS** – overall website design
- **HTML5 Canvas** – draws the course, players and balls

### Backend (Python)
- **Simulation engine** - Written in Python, handles the logic of the project
- **FastAPI** – WebSocket API for communication with frontend
- **Artificial intelligence agents**:
  - **Player agents** (utility-based)
  - **Greenkeeper agent** (rule-based)
  - **Wind agent** (stochastic)

---

## **Getting Started**

### Quick Start - Docker (Recommended)

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

### Quick Start - Local Development

Once dependencies are installed, run both servers simultaneously:

```bash
make dev
```

### Backend Setup

1. Create and activate a virtual environment:

   ```bash
   python3.11 -m venv venv
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

**Navigation Path Cache:**

The backend includes a pre-computed navigation path cache (`backend/data/navigation_path_cache.json`) for instant startups. The cache must be regenerated if you modify the course layout.

- **Delete cache when changing:** Water polygons, bridge positions, or green locations

To force path recomputation:
```bash
rm backend/data/navigation_path_cache.json
```

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
