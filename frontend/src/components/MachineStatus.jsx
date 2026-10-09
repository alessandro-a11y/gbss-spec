import { Card, Empty, fmtDate } from './ui'

const STATUS = {
  online: { label: 'Online', dot: 'bg-emerald-400', text: 'text-emerald-300' },
  offline: { label: 'Offline', dot: 'bg-slate-500', text: 'text-slate-400' },
  under_attack: { label: 'Sob ataque', dot: 'animate-pulse bg-red-500', text: 'text-red-300' },
}
const ROLE = { attacker: 'Atacante', victim: 'Vítima', soc: 'SOC' }

export default function MachineStatus({ machines = [] }) {
  return (
    <Card title="Máquinas do laboratório">
      {machines.length === 0 ? (
        <Empty>Nenhuma máquina registrada ainda.</Empty>
      ) : (
        <div className="grid gap-3 sm:grid-cols-3">
          {machines.map((m) => {
            const s = STATUS[m.status] || STATUS.offline
            return (
              <div key={m.hostname} className="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{m.hostname}</span>
                  <span className={`flex items-center gap-1.5 text-sm ${s.text}`}>
                    <span className={`h-2 w-2 rounded-full ${s.dot}`} />
                    {s.label}
                  </span>
                </div>
                <p className="mt-1 text-sm text-slate-400">{ROLE[m.role] || m.role} · {m.ip}</p>
                <p className="mt-1 text-xs text-slate-500">Visto: {fmtDate(m.last_seen)}</p>
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}