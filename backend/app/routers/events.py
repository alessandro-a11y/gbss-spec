import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import API_KEY
from app.database import get_db
from app.models import Event
from app.schemas import EventIn, EventOut
from app.services.ingest_service import ingest_event

router = APIRouter(prefix="/events", tags=["events"])


def require_api_key(x_api_key: str = Header(default="")) -> None:
    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key invalida")


@router.post("", response_model=EventOut, status_code=201, dependencies=[Depends(require_api_key)])
async def create_event(payload: EventIn, db: Session = Depends(get_db)):
    """Rota usada pelos agentes pra enviar eventos."""
    return await ingest_event(db, payload)


@router.get("", response_model=list[EventOut])
def list_events(
    db: Session = Depends(get_db),
    start: datetime | None = None,
    end: datetime | None = None,
    ip: str | None = Query(None, description="IP atacante ou vitima"),
    attack_type: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Listagem de logs com filtros por data, IP e tipo de ataque."""
    q = select(Event).order_by(Event.timestamp.desc())
    if start:
        q = q.where(Event.timestamp >= start)
    if end:
        q = q.where(Event.timestamp <= end)
    if ip:
        q = q.where(or_(Event.source_ip == ip, Event.target_ip == ip))
    if attack_type:
        q = q.where(Event.attack_type == attack_type)
    return db.scalars(q.limit(limit).offset(offset)).all()