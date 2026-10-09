import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Empty } from './ui'

export default function AttackVolumeChart({ timeline = [] }) {
  if (timeline.length === 0) return <Empty>Sem dados no período.</Empty>

  const data = timeline.map((t) => ({
    time: new Date(t.time).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
    ataques: t.count,
  }))

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="vol" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.5} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
          <XAxis dataKey="time" stroke="#64748b" fontSize={12} />
          <YAxis allowDecimals={false} stroke="#64748b" fontSize={12} />
          <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
          <Area type="monotone" dataKey="ataques" stroke="#ef4444" fill="url(#vol)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}