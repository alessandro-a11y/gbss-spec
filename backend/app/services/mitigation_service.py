from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DefenseAction, Machine
from app.schemas import ActionOut
from app.ws import manager


async def _broadcast(row: DefenseAction) -> ActionOut:
    out = ActionOut.model_validate(row)
    await manager.broadcast({"type": "action", "data": out.model_dump(mode="json")})
    return out


async def create_action(db: Session, ip: str, action: str, executed_by: str, status: str) -> ActionOut:
    if action == "block":
        protected = db.scalar(
            select(Machine).where(Machine.ip == ip, Machine.role.in_(["soc", "victim"]))
        )
        if protected:
            raise HTTPException(400, "Nao e permitido bloquear maquinas do proprio lab")

    row = DefenseAction(ip=ip, action=action, executed_by=executed_by, status=status)
    db.add(row)
    db.commit()
    db.refresh(row)
    return await _broadcast(row)


async def update_status(db: Session, action_id: int, status: str) -> ActionOut:
    row = db.get(DefenseAction, action_id)
    if not row:
        raise HTTPException(404, "Acao nao encontrada")
    row.status = status
    db.commit()
    db.refresh(row)
    return await _broadcast(row)


def pending_actions(db: Session) -> list[DefenseAction]:
    q = select(DefenseAction).where(DefenseAction.status == "pending").order_by(DefenseAction.id)
    return list(db.scalars(q).all())


def blocked_ips(db: Session) -> list[str]:
    """IPs cujo ultimo comando valido foi 'block' (inclui pendentes)."""
    q = select(DefenseAction).where(DefenseAction.status != "failed").order_by(DefenseAction.id)
    state: dict[str, str] = {}
    for row in db.scalars(q).all():
        state[row.ip] = row.action
    return sorted(ip for ip, act in state.items() if act == "block")