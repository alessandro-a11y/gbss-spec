from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Event(Base):
    """Um evento de ataque/alerta recebido de um agente."""
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    source_ip: Mapped[str] = mapped_column(String(45), index=True)    # atacante
    target_ip: Mapped[str] = mapped_column(String(45))                # vitima
    target_host: Mapped[str] = mapped_column(String(100), default="")
    attack_type: Mapped[str] = mapped_column(String(50), index=True)  # ex: brute_force_rdp
    severity: Mapped[str] = mapped_column(String(10), default="medium")  # low|medium|high|critical
    details: Mapped[str] = mapped_column(Text, default="")


class Machine(Base):
    """Maquina monitorada do laboratorio."""
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hostname: Mapped[str] = mapped_column(String(100), unique=True)
    ip: Mapped[str] = mapped_column(String(45))
    role: Mapped[str] = mapped_column(String(20))                     # attacker|victim|soc
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DefenseAction(Base):
    """Historico de acoes de mitigacao (bloqueio/desbloqueio de IP)."""
    __tablename__ = "defense_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    ip: Mapped[str] = mapped_column(String(45), index=True)
    action: Mapped[str] = mapped_column(String(10))                   # block|unblock
    status: Mapped[str] = mapped_column(String(10), default="success")  # success|failed
    executed_by: Mapped[str] = mapped_column(String(50), default="auto")  # auto|manual