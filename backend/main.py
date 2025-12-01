from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import json

from backend.loader import regenerate_course_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    regenerate_course_data()
    yield  # Separate startup and shutdown (shutdown after yield)


app = FastAPI(lifespan=lifespan)

# Configure CORS
# TODO: UPDATE LATER
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/holes/{hole_number}")
async def get_hole(hole_number: int):
    """Fetch hole data by hole number."""
    course_data_dir = Path(__file__).parent / "data" / "course"
    hole_file = course_data_dir / f"hole_{hole_number:02d}.json"

    if not hole_file.exists():
        raise HTTPException(status_code=404, detail=f"Hole {hole_number} not found")

    with open(hole_file, "r") as f:
        hole_data = json.load(f)

    return hole_data
