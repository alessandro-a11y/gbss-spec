import { Empty, SEVERITY, fmtDate } from './ui'

export default function AlertsTable({ events = [], onPickIp }) {
  if (events.length === 0) return <Empty>Nenhum evento encontrado.</Empty>

  return (
    <div className="max-h-96 overflow-auto">
      <table className="w-full text-left text-sm">
        <thead className="sticky top-0 bg-slate-900 text-xs uppercase text-slate-400">
          <tr>
            <th className="px-2 py-2">Data/hora</th>
            <th className="px-2 py-2">IP atacante</th>
            <th className="px-2 py-2">IP vítima</th>
            <th className="px-2 py-2">Tipo</th>
            <th className="px-2 py-2">Severidade</th>
            <th className="px-2 py-2">Detalhes</th>
          </tr>
        </thead>
        <tbody>
          {events.map((e) => (
            <tr key={e.id} className="border-t border-slate-800 hover:bg-slate-800/40">
              <td className="whitespace-nowrap px-2 py-2 text-slate-300">{fmtDate(e.timestamp)}</td>
              <td className="px-2 py-2 font-mono">
                <button className="hover:text-emerald-400 hover:underline" onClick={() => onPickIp?.(e.source_ip)} title="Usar no painel de mitigação">
                  {e.source_ip}
                </button>
              </td>
              <td className="px-2 py-2 font-mono text-slate-300">
                {e.target_ip} <span className="text-slate-500">{e.target_host && `(${e.target_host})`}</span>
              </td>
              <td className="px-2 py-2">{e.attack_type}</td>
              <td className="px-2 py-2">
                <span className={`rounded px-2 py-0.5 text-xs font-semibold ${SEVERITY[e.severity]}`}>{e.severity}</span>
              </td>
              <td className="px-2 py-2 text-slate-400">{e.details}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}