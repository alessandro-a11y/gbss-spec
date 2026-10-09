import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Empty } from './ui'

export default function AttackTypesChart({ types = [] }) {
  if (types.length === 0) return <Empty>Sem dados no período.</Empty>

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={types} layout="vertical" margin={{ left: 20 }}>
          <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
          <XAxis type="number" allowDecimals={false} stroke="#64748b" fontSize={12} />
          <YAxis type="category" dataKey="attack_type" stroke="#64748b" fontSize={12} width={130} />
          <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
          <Bar dataKey="count" name="ocorrências" fill="#f59e0b" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}