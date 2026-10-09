from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401  (registra as tabelas)
from app.config import CORS_ORIGINS
from app.database import Base, engine
from app.routers import events, agents, mitigation, reports
from app.ws import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="OxeTech Watchers", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(agents.router)
app.include_router(mitigation.router)
app.include_router(reports.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantem a conexao aberta
    except WebSocketDisconnect:
        manager.disconnect(websocket)