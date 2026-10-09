# OxeTech Watchers

Dashboard próprio de monitoramento e mitigação de ataques para laboratório de SOC.

## Arquitetura

| Máquina | Função | O que roda |
|---|---|---|
| Kali Linux | Atacante | Hydra + `kali_heartbeat.sh` |
| Windows (vítima) | Alvo | `agent/agent.py` (detecção e bloqueio) |
| Windows (SOC) | Painel | back-end FastAPI + front React |

Fluxo: o agente lê falhas de logon (evento 4625) → detecta brute force por regra
(N falhas do mesmo IP em X segundos) → `POST /events` → back-end grava e envia por
WebSocket → o dashboard atualiza ao vivo. Bloqueios podem ser automáticos (agente)
ou manuais (botão no dashboard → agente executa e confirma).

## Como rodar

### SOC (back-end)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# crie backend\.env com DATABASE_URL, API_KEY e CORS_ORIGINS (veja .env.example)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Libere a porta 8000 no firewall do Windows.

### SOC (front-end)
```powershell
cd frontend
npm install
npm run dev
```
Abra `http://localhost:5173`.

### Vítima (PowerShell como Administrador)
```powershell
auditpol /set /subcategory:"{0CCE9215-69AE-11D9-BED3-505054503030}" /failure:enable
cd agent
$env:OXE_API_URL = "http://IP_DO_SOC:8000"
$env:OXE_API_KEY = "SUA_CHAVE"
$env:OXE_WHITELIST = "IP_DO_SOC"
$env:OXE_AUTO_BLOCK = "1"   # 0 = só detecta, 1 = bloqueia sozinho
python agent.py
```
Variáveis opcionais: `OXE_THRESHOLD` (padrão 5), `OXE_WINDOW` (padrão 60s), `OXE_MY_IP`.

### Kali
```bash
./kali_heartbeat.sh IP_DO_SOC IP_DO_KALI SUA_CHAVE
```

## Funcionalidades

- Monitoramento em tempo real (WebSocket)
- Listagem de logs com filtro por data, IP e tipo de ataque
- Gráficos de volume no tempo e de tipos mais frequentes
- Status das máquinas (online, offline, sob ataque)
- Painel de mitigação (bloqueio/desbloqueio e histórico de defesa)
- Exportação de relatório em PDF

## Segurança

- Rotas de escrita dos agentes exigem o header `X-API-Key`.
- IPs são validados antes de qualquer comando de firewall; o agente não executa comandos via shell.
- Máquinas do próprio laboratório não podem ser bloqueadas pelo dashboard.
- Projeto de laboratório: não exponha a API na internet.