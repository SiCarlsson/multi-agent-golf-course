from fastapi import FastAPI
from contextlib import asynccontextmanager

from backend.loader import regenerate_course_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events."""
    regenerate_course_data()
    yield # Separate startup and shutdown (shutdown after yield)


app = FastAPI(lifespan=lifespan)
