import json
import random
import asyncio
import logging

from typing import Set
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from backend.loader import regenerate_course_data
from backend.simulation import SimulationEngine
from backend.simulation.player_group import PlayerGroup
from backend.agents import PlayerAgent, GreenkeeperAgent, WindAgent
from backend.constants import TICK_INTERVAL_SECONDS

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

simulation_engine = None
simulation_task = None
active_connections: Set[WebSocket] = set()


async def broadcast_game_state(game_state=None):
    """Broadcast game state to all connected clients."""
    if simulation_engine and active_connections:
        if game_state is None:
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

        if simulation_engine:
            logger.info("TICK")
            game_state = simulation_engine.tick()
            await broadcast_game_state(game_state)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    global simulation_engine, simulation_task
    regenerate_course_data()

    simulation_engine = SimulationEngine()

    greenkeeper = GreenkeeperAgent(
        id=1, 
        num_holes=simulation_engine.num_holes, 
        holes_data=simulation_engine.holes,
        navigation_paths=simulation_engine.greenkeeper_paths,
        water=simulation_engine.water,
        bridges=simulation_engine.bridges
    )
    simulation_engine.greenkeeper = greenkeeper

    wind_agent = WindAgent()
    simulation_engine.wind_agent = wind_agent

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

        # Load course-wide features
        course_features = {}
        for feature_name in ["water", "bridges"]:
            feature_file = course_data_dir / f"{feature_name}.json"
            with open(feature_file, "r") as f:
                feature_json = json.load(f)
                course_features[feature_name] = feature_json.get(feature_name, [])

        await websocket.send_text(
            json.dumps(
                {
                    "type": "course_data",
                    "data": {
                        "holes": holes,
                        **course_features,
                        "tick_interval": TICK_INTERVAL_SECONDS,
                    },
                }
            )
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
