from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Set

app = FastAPI()

# Monta archivos estáticos (sirve index.html)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Estructura en memoria: room -> set de websockets
rooms: Dict[str, Set[WebSocket]] = {}

@app.get("/")
async def root():
    return HTMLResponse('<!doctype html><meta http-equiv="refresh" content="0; url=/static/index.html">')

@app.websocket("/ws/{room}")
async def ws_endpoint(websocket: WebSocket, room: str):
    await websocket.accept()
    if room not in rooms:
        rooms[room] = set()
    rooms[room].add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Reenvía el mensaje a todos los demás en la sala
            dead = []
            for peer in rooms[room]:
                if peer is websocket:
                    continue
                try:
                    await peer.send_text(data)
                except Exception:
                    dead.append(peer)
            for d in dead:
                rooms[room].discard(d)
    except WebSocketDisconnect:
        pass
    finally:
        rooms[room].discard(websocket)
        if not rooms[room]:
            del rooms[room]