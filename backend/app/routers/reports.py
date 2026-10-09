from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.report_service import build_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/pdf")
def pdf_report(minutes: int = Query(60, ge=5, le=10080), db: Session = Depends(get_db)):
    """Relatorio em PDF do periodo (ultimos N minutos)."""
    data = build_report(db, minutes)
    filename = f"oxetech-relatorio-{datetime.now():%Y%m%d-%H%M}.pdf"
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )