import json
import asyncio
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path

from backend.loader import regenerate_course_data
from backend.simulation import SimulationEngine
from backend.simulation.player_group import PlayerGroup
from backend.agents import PlayerAgent
from backend.constants import TICK_INTERVAL_SECONDS

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global simulation instance
simulation_engine = None
simulation_task = None


async def run_simulation():
    """Background task that runs the simulation."""
    global simulation_engine

    while True:
        await asyncio.sleep(TICK_INTERVAL_SECONDS)

        if simulation_engine and simulation_engine.player_groups:
            # Tick the simulation if not complete
            if not all(g.is_complete for g in simulation_engine.player_groups):
                logger.info("TICK")
                simulation_engine.tick()
            else:
                logger.info("Simulation complete for all groups.")
                break


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    global simulation_engine, simulation_task
    regenerate_course_data()

    # Initialize simulation engine with one player
    simulation_engine = SimulationEngine()
    player = PlayerAgent(id=1, accuracy=0.8, strength=0.9)
    group = PlayerGroup(id=1, players=[player], starting_hole=1, tee_time=0)

    # Position player and ball at tee
    tee_box = simulation_engine.holes[1]["tees"][0]
    tee_position = simulation_engine.get_tee_position(tee_box)
    player.player_position = tee_position
    player.ball_position = tee_position.copy()

    simulation_engine.player_groups.append(group)

    # Start background simulation task
    simulation_task = asyncio.create_task(run_simulation())

    yield

    # Cleanup on shutdown
    if simulation_task:
        simulation_task.cancel()


app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/holes")
async def get_all_holes():
    """Fetch all hole data."""
    course_data_dir = Path(__file__).parent / "data" / "course"

    holes = []
    hole_files = sorted(course_data_dir.glob("hole_*.json"))

    if not hole_files:
        raise HTTPException(status_code=404, detail="No holes found")

    for hole_file in hole_files:
        with open(hole_file, "r") as f:
            hole_data = json.load(f)
            holes.append(hole_data)

    return {"holes": holes}


@app.get("/api/gamestate")
async def get_game_state():
    """Get current simulation state."""
    return simulation_engine.get_state()
