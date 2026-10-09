import io
from collections import Counter
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DefenseAction, Event, Machine

MAX_EVENT_ROWS = 60
SEVERITY_ORDER = ["critical", "high", "medium", "low"]


def _local(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone().strftime("%d/%m/%Y %H:%M:%S")


def _table(rows: list[list], widths: list[float]) -> Table:
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
    ]))
    return t


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1.2 * cm, "OxeTech Watchers - relatorio de seguranca")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Pagina {doc.page}")
    canvas.restoreState()


def build_report(db: Session, minutes: int) -> bytes:
    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=minutes)

    events = db.scalars(
        select(Event).where(Event.timestamp >= since).order_by(Event.timestamp.desc())
    ).all()
    actions = db.scalars(
        select(DefenseAction).where(DefenseAction.timestamp >= since).order_by(DefenseAction.timestamp.desc())
    ).all()
    machines = db.scalars(select(Machine).order_by(Machine.hostname)).all()

    styles = getSampleStyleSheet()
    cell = ParagraphStyle("cell", parent=styles["BodyText"], fontSize=8, leading=10)
    h2 = styles["Heading2"]

    def P(text) -> Paragraph:
        return Paragraph(escape(str(text)), cell)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title="OxeTech Watchers - Relatorio", author="OxeTech Watchers",
    )
    story = [
        Paragraph("OxeTech Watchers", styles["Title"]),
        Paragraph("Relatorio de ataques e acoes de defesa", styles["Heading3"]),
        Paragraph(
            f"Periodo: {_local(since)} ate {_local(now)} (ultimos {minutes} min)<br/>Gerado em: {_local(now)}",
            styles["BodyText"],
        ),
        Spacer(1, 0.4 * cm),
    ]

    # Resumo
    by_sev = Counter(e.severity for e in events)
    summary = [["Indicador", "Valor"], ["Total de eventos", str(len(events))]]
    for sev in SEVERITY_ORDER:
        summary.append([f"Severidade {sev}", str(by_sev.get(sev, 0))])
    ok_actions = sum(1 for a in actions if a.status == "success")
    summary.append(["Acoes de defesa (sucesso / total)", f"{ok_actions} / {len(actions)}"])
    story += [Paragraph("Resumo", h2), _table(summary, [9 * cm, 4 * cm]), Spacer(1, 0.4 * cm)]

    # Tipos de ataque e IPs
    types = [["Tipo de ataque", "Ocorrencias"]] + [
        [t, str(c)] for t, c in Counter(e.attack_type for e in events).most_common(5)
    ]
    ips = [["IP atacante", "Ocorrencias"]] + [
        [ip, str(c)] for ip, c in Counter(e.source_ip for e in events).most_common(5)
    ]
    if len(events) == 0:
        types.append(["-", "0"])
        ips.append(["-", "0"])
    story += [
        Paragraph("Tipos de ataque mais frequentes", h2), _table(types, [9 * cm, 4 * cm]), Spacer(1, 0.3 * cm),
        Paragraph("Principais IPs atacantes", h2), _table(ips, [9 * cm, 4 * cm]), Spacer(1, 0.4 * cm),
    ]

    # Maquinas
    mrows = [["Maquina", "IP", "Papel", "Ultima atividade"]] + [
        [P(m.hostname), P(m.ip), P(m.role), P(_local(m.last_seen))] for m in machines
    ]
    story += [Paragraph("Maquinas monitoradas", h2), _table(mrows, [4 * cm, 3.5 * cm, 3 * cm, 5 * cm]), Spacer(1, 0.4 * cm)]

    # Eventos
    erows = [["Data/hora", "Atacante", "Vitima", "Tipo", "Sev.", "Detalhes"]]
    for e in events[:MAX_EVENT_ROWS]:
        erows.append([
            P(_local(e.timestamp)), P(e.source_ip), P(f"{e.target_ip} {e.target_host}".strip()),
            P(e.attack_type), P(e.severity), P(e.details),
        ])
    if len(events) == 0:
        erows.append([P("Nenhum evento no periodo."), "", "", "", "", ""])
    story += [
        Paragraph("Eventos", h2),
        _table(erows, [2.9 * cm, 2.3 * cm, 2.9 * cm, 2.6 * cm, 1.4 * cm, 4.9 * cm]),
    ]
    if len(events) > MAX_EVENT_ROWS:
        story.append(Paragraph(f"Mostrando os {MAX_EVENT_ROWS} mais recentes de {len(events)} eventos.", styles["Italic"]))
    story.append(Spacer(1, 0.4 * cm))

    # Acoes de defesa
    arows = [["Data/hora", "IP", "Acao", "Origem", "Status"]]
    for a in actions:
        arows.append([
            P(_local(a.timestamp)), P(a.ip), P("Bloqueio" if a.action == "block" else "Desbloqueio"),
            P("automatica" if a.executed_by == "auto" else "manual"), P(a.status),
        ])
    if len(actions) == 0:
        arows.append([P("Nenhuma acao no periodo."), "", "", "", ""])
    story += [Paragraph("Acoes de defesa", h2), _table(arows, [3.8 * cm, 3.2 * cm, 3 * cm, 3 * cm, 3 * cm])]

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()