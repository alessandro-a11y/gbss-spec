import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import { useAlertsSocket } from './hooks/useAlertsSocket'

export default function App() {
  const { connected } = useAlertsSocket()

  return (
    <Layout connected={connected}>
      <Dashboard />
    </Layout>
  )
}