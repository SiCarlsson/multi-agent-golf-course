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
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET"],
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