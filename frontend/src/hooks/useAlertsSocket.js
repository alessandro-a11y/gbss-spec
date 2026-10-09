import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { WS_URL } from '../services/api'

/**
 * Mantem o WebSocket aberto (com reconexao automatica) e, a cada mensagem,
 * manda o React Query rebuscar os dados afetados.
 */
export function useAlertsSocket() {
  const qc = useQueryClient()
  const [connected, setConnected] = useState(false)
  const [lastEvent, setLastEvent] = useState(null)

  useEffect(() => {
    let ws
    let timer
    let closed = false

    const connect = () => {
      ws = new WebSocket(WS_URL)
      ws.onopen = () => setConnected(true)
      ws.onmessage = (msg) => {
        const m = JSON.parse(msg.data)
        if (m.type === 'event') {
          setLastEvent(m.data)
          qc.invalidateQueries({ queryKey: ['events'] })
          qc.invalidateQueries({ queryKey: ['stats'] })
          qc.invalidateQueries({ queryKey: ['machines'] })
        }
        if (m.type === 'action') {
          qc.invalidateQueries({ queryKey: ['actions'] })
          qc.invalidateQueries({ queryKey: ['blocked'] })
        }
      }
      ws.onclose = () => {
        setConnected(false)
        if (!closed) timer = setTimeout(connect, 2000)
      }
      ws.onerror = () => ws.close()
    }

    connect()
    return () => {
      closed = true
      clearTimeout(timer)
      if (ws) ws.close()
    }
  }, [qc])

  return { connected, lastEvent }
}