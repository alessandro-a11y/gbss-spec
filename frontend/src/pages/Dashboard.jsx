import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { API_URL, getBlocked, getEvents, getMachines, getStats } from '../services/api'
import { Card, Stat } from '../components/ui'
import MachineStatus from '../components/MachineStatus'
import Filters from '../components/Filters'
import AlertsTable from '../components/AlertsTable'
import AttackVolumeChart from '../components/AttackVolumeChart'
import AttackTypesChart from '../components/AttackTypesChart'
import MitigationPanel from '../components/MitigationPanel'

const toIso = (v) => (v ? new Date(v).toISOString() : '')

export default function Dashboard() {
  const [filters, setFilters] = useState({ ip: '', attack_type: '', start: '', end: '' })
  const [minutes, setMinutes] = useState(60)
  const [pickedIp, setPickedIp] = useState('')

  const params = { ...filters, start: toIso(filters.start), end: toIso(filters.end), limit: 100 }

  const events = useQuery({ queryKey: ['events', params], queryFn: () => getEvents(params) })
  const stats = useQuery({ queryKey: ['stats', minutes], queryFn: () => getStats(minutes), refetchInterval: 30000 })
  const machines = useQuery({ queryKey: ['machines'], queryFn: getMachines, refetchInterval: 15000 })
  const blocked = useQuery({ queryKey: ['blocked'], queryFn: getBlocked })

  const s = stats.data
  const critical = (s?.by_severity?.critical || 0) + (s?.by_severity?.high || 0)
  const underAttack = (machines.data || []).filter((m) => m.status === 'under_attack').length
  const typeNames = (s?.top_attack_types || []).map((t) => t.attack_type)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-end gap-3 text-sm text-slate-400">
        Período:
        <select
          value={minutes}
          onChange={(e) => setMinutes(Number(e.target.value))}
          className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1"
        >
          <option value={15}>15 min</option>
          <option value={60}>1 hora</option>
          <option value={360}>6 horas</option>
          <option value={1440}>24 horas</option>
        </select>
        <button
          onClick={() => window.open(`${API_URL}/reports/pdf?minutes=${minutes}`, '_blank')}
          className="rounded-md bg-emerald-600 px-3 py-1.5 font-semibold text-white hover:bg-emerald-500"
        >
          Exportar PDF
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Eventos no período" value={s?.total ?? '–'} />
        <Stat label="Alta / crítica" value={s ? critical : '–'} tone="text-orange-400" />
        <Stat label="Máquinas sob ataque" value={underAttack} tone={underAttack ? 'text-red-400' : 'text-emerald-400'} />
        <Stat label="IPs bloqueados" value={blocked.data?.length ?? '–'} tone="text-sky-400" />
      </div>

      <MachineStatus machines={machines.data} />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Volume de ataques no tempo">
          <AttackVolumeChart timeline={s?.timeline} />
        </Card>
        <Card title="Tipos de ataque mais frequentes">
          <AttackTypesChart types={s?.top_attack_types} />
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Logs de eventos" className="lg:col-span-2">
          <Filters value={filters} onChange={setFilters} attackTypes={typeNames} />
          <div className="mt-4">
            <AlertsTable events={events.data} onPickIp={setPickedIp} />
          </div>
        </Card>
        <MitigationPanel suggestedIp={pickedIp} />
      </div>
    </div>
  )
}