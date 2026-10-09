from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Event, Machine
from app.routers.events import require_api_key
from app.schemas import HeartbeatIn, MachineOut

router = APIRouter(tags=["monitoring"])

OFFLINE_AFTER = timedelta(seconds=60)
ATTACK_WINDOW = timedelta(seconds=60)


def _aware(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


@router.post("/machines/heartbeat", status_code=204, dependencies=[Depends(require_api_key)])
def heartbeat(payload: HeartbeatIn, db: Session = Depends(get_db)):
    """Cada agente chama isso a cada ~15s pra aparecer como online."""
    now = datetime.now(timezone.utc)
    m = db.scalar(select(Machine).where(Machine.hostname == payload.hostname))
    if m:
        m.ip, m.role, m.last_seen = payload.ip, payload.role, now
    else:
        db.add(Machine(hostname=payload.hostname, ip=payload.ip, role=payload.role, last_seen=now))
    db.commit()


@router.get("/machines", response_model=list[MachineOut])
def list_machines(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    under_attack = set(
        db.scalars(select(Event.target_host).where(Event.timestamp >= now - ATTACK_WINDOW)).all()
    )
    result = []
    for m in db.scalars(select(Machine).order_by(Machine.hostname)).all():
        seen = _aware(m.last_seen)
        if m.hostname in under_attack:
            status = "under_attack"
        elif now - seen > OFFLINE_AFTER:
            status = "offline"
        else:
            status = "online"
        result.append(MachineOut(hostname=m.hostname, ip=m.ip, role=m.role, last_seen=seen, status=status))
    return result


@router.get("/stats")
def stats(minutes: int = Query(60, ge=5, le=1440), db: Session = Depends(get_db)):
    """Dados prontos pros graficos: volume no tempo, tipos mais frequentes, totais."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=minutes)
    events = db.scalars(select(Event).where(Event.timestamp >= since)).all()

    step = 1 if minutes <= 120 else 10

    def floor(dt: datetime) -> datetime:
        dt = dt.replace(second=0, microsecond=0)
        return dt.replace(minute=dt.minute - dt.minute % step)

    buckets: dict[datetime, int] = {}
    cur, end = floor(since), floor(now)
    while cur <= end:
        buckets[cur] = 0
        cur += timedelta(minutes=step)
    for e in events:
        key = floor(_aware(e.timestamp))
        if key in buckets:
            buckets[key] += 1

    return {
        "total": len(events),
        "by_severity": dict(Counter(e.severity for e in events)),
        "top_attack_types": [
            {"attack_type": t, "count": c} for t, c in Counter(e.attack_type for e in events).most_common(5)
        ],
        "top_source_ips": [
            {"ip": ip, "count": c} for ip, c in Counter(e.source_ip for e in events).most_common(5)
        ],
        "timeline": [{"time": k.isoformat(), "count": v} for k, v in buckets.items()],
    }