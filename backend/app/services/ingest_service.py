from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Event, Machine
from app.schemas import EventIn, EventOut
from app.ws import manager


def _to_utc(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(timezone.utc)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _touch_machine(db: Session, hostname: str, ip: str) -> None:
    """Atualiza (ou cria) a maquina alvo e marca 'visto agora'."""
    if not hostname:
        return
    machine = db.scalar(select(Machine).where(Machine.hostname == hostname))
    now = datetime.now(timezone.utc)
    if machine:
        machine.ip = ip
        machine.last_seen = now
    else:
        db.add(Machine(hostname=hostname, ip=ip, role="victim", last_seen=now))


async def ingest_event(db: Session, payload: EventIn) -> EventOut:
    """Valida, salva no banco e repassa pro dashboard em tempo real."""
    event = Event(
        timestamp=_to_utc(payload.timestamp),
        source_ip=payload.source_ip,
        target_ip=payload.target_ip,
        target_host=payload.target_host,
        attack_type=payload.attack_type,
        severity=payload.severity,
        details=payload.details,
    )
    db.add(event)
    _touch_machine(db, payload.target_host, payload.target_ip)
    db.commit()
    db.refresh(event)

    out = EventOut.model_validate(event)
    await manager.broadcast({"type": "event", "data": out.model_dump(mode="json")})
    return out