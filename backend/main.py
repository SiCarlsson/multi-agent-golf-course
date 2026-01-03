import json
import asyncio
import logging

from typing import Set
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

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
active_connections: Set[WebSocket] = set()


async def broadcast_game_state():
    """Broadcast game state to all connected clients."""
    if simulation_engine and active_connections:
        game_state = simulation_engine.get_state()
        message = json.dumps({"type": "gamestate", "data": game_state})

        disconnected = set()
        for connection in active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(connection)

        active_connections.difference_update(disconnected)


async def run_simulation():
    """Background task that runs the simulation."""
    global simulation_engine

    while True:
        await asyncio.sleep(TICK_INTERVAL_SECONDS)

        if simulation_engine and simulation_engine.player_groups:
            if not all(group.is_complete for group in simulation_engine.player_groups):
                logger.info("TICK")
                simulation_engine.tick()
                await broadcast_game_state()
            else:
                logger.info("Simulation complete for all groups.")
                break


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    global simulation_engine, simulation_task
    regenerate_course_data()

    simulation_engine = SimulationEngine()

    # Sample player and group
    player_1 = PlayerAgent(id=1, accuracy=0.2, strength=0.85)
    player_2 = PlayerAgent(id=2, accuracy=1.0, strength=0.85)
    group = PlayerGroup(id=1, players=[player_1, player_2], starting_hole=1, tee_time=0)

    # Position player and ball at tee
    tee_box = simulation_engine.holes[1]["tees"][3]
    tee_position = simulation_engine.get_tee_position(tee_box)
    player_1.player_position = tee_position.copy()
    player_1.ball_position = tee_position.copy()
    player_2.player_position = tee_position.copy()
    player_2.ball_position = tee_position.copy()

    simulation_engine.player_groups.append(group)

    simulation_task = asyncio.create_task(run_simulation())

    yield

    # Cleanup on shutdown
    if simulation_task:
        simulation_task.cancel()


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time game state updates."""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"Client connected. Total connections: {len(active_connections)}")

    try:
        course_data_dir = Path(__file__).parent / "data" / "course"
        holes = []
        hole_files = sorted(course_data_dir.glob("hole_*.json"))

        for hole_file in hole_files:
            with open(hole_file, "r") as f:
                hole_data = json.load(f)
                holes.append(hole_data)

        await websocket.send_text(
            json.dumps({
                "type": "course_data", 
                "data": {
                    "holes": holes,
                    "tick_interval": TICK_INTERVAL_SECONDS
                }
            })
        )

        if simulation_engine:
            game_state = simulation_engine.get_state()
            await websocket.send_text(
                json.dumps({"type": "gamestate", "data": game_state})
            )

        while True:
            data = await websocket.receive_text()
            logger.info(f"Received message from client: {data}")

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)
        logger.info(f"Client removed. Total connections: {len(active_connections)}")
