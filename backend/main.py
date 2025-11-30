from fastapi import FastAPI, WebSocket
from backend.loader import load_hole

app = FastAPI()

# Load hole
hole1 = load_hole("backend/course/hole_1.json")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        # send hole geometry and ball/agent state
        await ws.send_json({"hole": hole1, "ball": {"x": 50, "y": 50}})
