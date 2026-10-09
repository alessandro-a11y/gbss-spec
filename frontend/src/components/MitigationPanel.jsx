import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getActions, getBlocked, requestAction } from '../services/api'
import { Card, Empty, fmtDate } from './ui'

const STATUS_STYLE = {
  pending: 'bg-amber-500/15 text-amber-300',
  success: 'bg-emerald-500/15 text-emerald-300',
  failed: 'bg-red-500/20 text-red-300',
}

export default function MitigationPanel({ suggestedIp }) {
  const qc = useQueryClient()
  const [ip, setIp] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    if (suggestedIp) setIp(suggestedIp)
  }, [suggestedIp])

  const blocked = useQuery({ queryKey: ['blocked'], queryFn: getBlocked })
  const actions = useQuery({ queryKey: ['actions'], queryFn: getActions })

  const mutation = useMutation({
    mutationFn: ({ ip, action }) => requestAction(ip, action),
    onSuccess: () => {
      setError('')
      qc.invalidateQueries({ queryKey: ['actions'] })
      qc.invalidateQueries({ queryKey: ['blocked'] })
    },
    onError: (err) => {
      const d = err.response?.data?.detail
      setError(typeof d === 'string' ? d : 'IP inválido ou erro no servidor.')
    },
  })

  return (
    <Card title="Painel de mitigação">
      <div className="flex gap-2">
        <input
          value={ip}
          onChange={(e) => setIp(e.target.value)}
          placeholder="IP a bloquear (ex.: 192.168.0.50)"
          className="flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm outline-none focus:border-red-500"
        />
        <button
          disabled={!ip.trim() || mutation.isPending}
          onClick={() => mutation.mutate({ ip: ip.trim(), action: 'block' })}
          className="rounded-md bg-red-600 px-4 py-2 text-sm font-semibold hover:bg-red-500 disabled:opacity-40"
        >
          Bloquear
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}

      <h3 className="mb-2 mt-4 text-sm font-semibold text-slate-300">IPs bloqueados</h3>
      {(blocked.data || []).length === 0 ? (
        <Empty>Nenhum IP bloqueado.</Empty>
      ) : (
        <ul className="space-y-1">
          {blocked.data.map((b) => (
            <li key={b} className="flex items-center justify-between rounded-md bg-slate-950/50 px-3 py-1.5">
              <span className="font-mono text-sm">{b}</span>
              <button
                onClick={() => mutation.mutate({ ip: b, action: 'unblock' })}
                className="text-xs text-slate-400 hover:text-emerald-400"
              >
                Desbloquear
              </button>
            </li>
          ))}
        </ul>
      )}

      <h3 className="mb-2 mt-4 text-sm font-semibold text-slate-300">Histórico de defesa</h3>
      {(actions.data || []).length === 0 ? (
        <Empty>Nenhuma ação registrada.</Empty>
      ) : (
        <div className="max-h-48 overflow-auto">
          <table className="w-full text-left text-xs">
            <tbody>
              {actions.data.map((a) => (
                <tr key={a.id} className="border-t border-slate-800">
                  <td className="py-1.5 pr-2 text-slate-400">{fmtDate(a.timestamp)}</td>
                  <td className="pr-2 font-mono">{a.ip}</td>
                  <td className="pr-2">{a.action === 'block' ? 'Bloqueio' : 'Desbloqueio'}</td>
                  <td className="pr-2 text-slate-500">{a.executed_by === 'auto' ? 'auto' : 'manual'}</td>
                  <td>
                    <span className={`rounded px-1.5 py-0.5 ${STATUS_STYLE[a.status]}`}>{a.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}