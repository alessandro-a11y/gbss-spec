from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DefenseAction
from app.routers.events import require_api_key
from app.schemas import ActionIn, ActionOut, ActionReport, StatusUpdate
from app.services import mitigation_service as svc

router = APIRouter(prefix="/mitigation", tags=["mitigation"])


@router.get("/actions", response_model=list[ActionOut])
def history(db: Session = Depends(get_db), limit: int = Query(100, ge=1, le=500)):
    """Historico de acoes de defesa."""
    q = select(DefenseAction).order_by(DefenseAction.timestamp.desc()).limit(limit)
    return db.scalars(q).all()


@router.get("/blocked", response_model=list[str])
def blocked(db: Session = Depends(get_db)):
    return svc.blocked_ips(db)


@router.post("/actions", response_model=ActionOut, status_code=201)
async def request_action(payload: ActionIn, db: Session = Depends(get_db)):
    """Dashboard pede bloqueio/desbloqueio. Fica 'pending' ate o agente executar."""
    return await svc.create_action(db, payload.ip, payload.action, "manual", "pending")


@router.get("/pending", response_model=list[ActionOut], dependencies=[Depends(require_api_key)])
def pending(db: Session = Depends(get_db)):
    """Agente consulta aqui o que precisa executar."""
    return svc.pending_actions(db)


@router.patch("/actions/{action_id}", response_model=ActionOut, dependencies=[Depends(require_api_key)])
async def update_action(action_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    """Agente confirma que executou (success) ou falhou (failed)."""
    return await svc.update_status(db, action_id, payload.status)


@router.post("/report", response_model=ActionOut, status_code=201, dependencies=[Depends(require_api_key)])
async def report_action(payload: ActionReport, db: Session = Depends(get_db)):
    """Agente reporta um bloqueio automatico que ele ja executou."""
    return await svc.create_action(db, payload.ip, payload.action, payload.executed_by, payload.status)