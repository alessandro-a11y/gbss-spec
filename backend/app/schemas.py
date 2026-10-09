from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal, Optional
import ipaddress

Severity = Literal["low", "medium", "high", "critical"]


class EventIn(BaseModel):
    """Payload que o agente envia no POST /events."""
    source_ip: str = Field(max_length=45)
    target_ip: str = Field(max_length=45)
    target_host: str = ""
    attack_type: str = Field(max_length=50)
    severity: Severity = "medium"
    details: str = ""
    timestamp: Optional[datetime] = None


class EventOut(EventIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime

    @field_validator("timestamp", mode="after")
    @classmethod
    def _force_utc(cls, v: datetime) -> datetime:
        return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v

class MachineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    hostname: str
    ip: str
    role: str
    last_seen: datetime
    status: str = "online"   # calculado: online|offline|under_attack


class ActionIn(BaseModel):
    ip: str = Field(max_length=45)
    action: Literal["block", "unblock"]
    executed_by: str = "manual"

    @field_validator("ip")
    @classmethod
    def _valid_ip(cls, v: str) -> str:
        try:
            return str(ipaddress.ip_address(v.strip()))
        except ValueError:
            raise ValueError("IP invalido")

class ActionOut(ActionIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime
    status: str

    @field_validator("timestamp", mode="after")
    @classmethod
    def _force_utc(cls, v: datetime) -> datetime:
        return v.replace(tzinfo=timezone.utc) if v.tzinfo is None else v

class ActionReport(ActionIn):
    """Agente reporta uma acao que ele mesmo executou (bloqueio automatico)."""
    executed_by: str = "auto"
    status: Literal["success", "failed"] = "success"


class StatusUpdate(BaseModel):
    status: Literal["success", "failed"]


class HeartbeatIn(BaseModel):
    hostname: str = Field(max_length=100)
    ip: str = Field(max_length=45)
    role: Literal["attacker", "victim", "soc"]