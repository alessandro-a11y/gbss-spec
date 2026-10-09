"""OxeTech Watchers - agente da maquina vitima (Windows).

- Le falhas de logon (evento 4625) do log de seguranca
- Detecta brute force por IP (N falhas em X segundos)
- Envia o evento ao back-end e (opcional) bloqueia o IP no firewall
- Executa bloqueios pedidos pelo dashboard e confirma o resultado
- Manda heartbeat para a maquina aparecer online

Precisa rodar como ADMINISTRADOR (log Security + netsh).
"""
import ipaddress
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict, deque
from datetime import datetime, timezone

API_URL = os.getenv("OXE_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("OXE_API_KEY", "")
HOSTNAME = os.getenv("OXE_HOSTNAME", socket.gethostname())
THRESHOLD = int(os.getenv("OXE_THRESHOLD", "5"))      # falhas ate considerar ataque
WINDOW = int(os.getenv("OXE_WINDOW", "60"))           # janela em segundos
POLL = int(os.getenv("OXE_POLL", "5"))                # intervalo de leitura
AUTO_BLOCK = os.getenv("OXE_AUTO_BLOCK", "1") == "1"  # bloqueio autonomo
WHITELIST = {x.strip() for x in os.getenv("OXE_WHITELIST", "").split(",") if x.strip()}


def detect_my_ip() -> str:
    if os.getenv("OXE_MY_IP"):
        return os.environ["OXE_MY_IP"]
    host = urllib.parse.urlparse(API_URL).hostname or "8.8.8.8"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((host, 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


MY_IP = detect_my_ip()

PS_SCRIPT = r"""
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$since = (Get-Date).AddSeconds(-__SECS__)
$ev = Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625;StartTime=$since} -ErrorAction SilentlyContinue
$out = foreach ($e in $ev) {
  $x = [xml]$e.ToXml()
  $d = @{}
  foreach ($n in $x.Event.EventData.Data) { $d[$n.Name] = $n.'#text' }
  [pscustomobject]@{
    id = $e.RecordId
    epoch = ([DateTimeOffset]$e.TimeCreated).ToUnixTimeSeconds()
    ip = $d['IpAddress']
    user = $d['TargetUserName']
    ltype = $d['LogonType']
  }
}
if ($out) { @($out) | ConvertTo-Json -Compress }
"""

seen: dict[int, float] = {}                       # RecordId -> epoch
fails: dict[str, deque] = defaultdict(deque)      # ip -> (epoch, user, logon_type)
alerted: dict[str, float] = {}                    # ip -> ultimo alerta
blocked_local: set[str] = set()


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def call(method: str, path: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API_URL + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "X-API-Key": API_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        log(f"[!] API {method} {path}: {e}")
        return None


def usable_ip(value: str) -> bool:
    """So IPs reais de terceiros. Ignora vazio, '-', loopback, whitelist e a propria maquina."""
    try:
        ip = ipaddress.ip_address((value or "").strip())
    except ValueError:
        return False
    if ip.is_loopback or ip.is_unspecified or ip.is_multicast:
        return False
    return str(ip) not in WHITELIST and str(ip) != MY_IP


def read_failed_logons(seconds: int) -> list[dict]:
    script = PS_SCRIPT.replace("__SECS__", str(int(seconds)))
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        log(f"[!] falha ao ler o log: {e}")
        return []
    out = r.stdout.strip()
    if not out:
        return []
    try:
        data = json.loads(out)
    except ValueError:
        return []
    return data if isinstance(data, list) else [data]


def firewall(action: str, ip: str) -> bool:
    """Bloqueia/desbloqueia via netsh. Sem shell, IP ja validado."""
    if not usable_ip(ip):
        return False
    name = f"OxeTech-Block-{ip}"
    delete = ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={name}"]
    if action == "block":
        subprocess.run(delete, capture_output=True)  # evita regra duplicada
        cmd = ["netsh", "advfirewall", "firewall", "add", "rule", f"name={name}",
               "dir=in", "action=block", f"remoteip={ip}"]
    else:
        cmd = delete
    ok = subprocess.run(cmd, capture_output=True).returncode == 0
    if ok:
        blocked_local.add(ip) if action == "block" else blocked_local.discard(ip)
    return ok


def alert(ip: str, dq: deque) -> None:
    count = len(dq)
    users = sorted({u for _, u, _ in dq if u})[:5]
    ltype = dq[-1][2]
    attack = {"10": "brute_force_rdp", "3": "brute_force_network"}.get(ltype, "brute_force_logon")
    severity = "critical" if count >= THRESHOLD * 3 else "high"
    log(f"ATAQUE: {attack} de {ip} ({count} falhas em {WINDOW}s)")

    call("POST", "/events", {
        "source_ip": ip,
        "target_ip": MY_IP,
        "target_host": HOSTNAME,
        "attack_type": attack,
        "severity": severity,
        "details": f"{count} falhas de logon em {WINDOW}s; usuarios tentados: {', '.join(users) or '-'}",
        "timestamp": datetime.fromtimestamp(dq[-1][0], timezone.utc).isoformat(),
    })

    if AUTO_BLOCK and ip not in blocked_local:
        ok = firewall("block", ip)
        log(f"bloqueio automatico de {ip}: {'ok' if ok else 'FALHOU'}")
        call("POST", "/mitigation/report", {
            "ip": ip, "action": "block", "executed_by": "auto",
            "status": "success" if ok else "failed",
        })


def process(events: list[dict]) -> None:
    now = time.time()
    for ev in events:
        rid = ev.get("id")
        if rid is None or rid in seen:
            continue
        seen[rid] = ev["epoch"]
        ip = (ev.get("ip") or "").strip()
        if usable_ip(ip):
            fails[ip].append((ev["epoch"], ev.get("user") or "", str(ev.get("ltype") or "")))

    for rid in [k for k, v in seen.items() if v < now - WINDOW * 3]:
        del seen[rid]

    for ip, dq in list(fails.items()):
        while dq and dq[0][0] < now - WINDOW:
            dq.popleft()
        if not dq:
            del fails[ip]
        elif len(dq) >= THRESHOLD and now - alerted.get(ip, 0) > WINDOW:
            alerted[ip] = now
            alert(ip, dq)


def handle_pending() -> None:
    """Executa bloqueios/desbloqueios pedidos pelo dashboard."""
    for a in call("GET", "/mitigation/pending") or []:
        ok = firewall(a["action"], a["ip"])
        log(f"acao do dashboard: {a['action']} {a['ip']} -> {'ok' if ok else 'FALHOU'}")
        call("PATCH", f"/mitigation/actions/{a['id']}", {"status": "success" if ok else "failed"})


def main() -> None:
    if not API_KEY:
        sys.exit("Defina OXE_API_KEY antes de rodar.")
    log(f"Agente {HOSTNAME} ({MY_IP}) -> {API_URL} | limite {THRESHOLD} falhas/{WINDOW}s | "
        f"bloqueio automatico: {'ligado' if AUTO_BLOCK else 'desligado'}")
    last_hb = 0.0
    while True:
        try:
            if time.time() - last_hb >= 15:
                call("POST", "/machines/heartbeat", {"hostname": HOSTNAME, "ip": MY_IP, "role": "victim"})
                last_hb = time.time()
            process(read_failed_logons(WINDOW + POLL))
            handle_pending()
        except Exception as e:  # o agente nao pode morrer
            log(f"[!] erro no ciclo: {e}")
        time.sleep(POLL)


if __name__ == "__main__":
    main()