import axios from 'axios'

// Usa o mesmo host de onde o front foi aberto (funciona em localhost e pelo IP da maquina SOC)
export const API_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`
export const WS_URL = API_URL.replace(/^http/, 'ws') + '/ws/events'

export const api = axios.create({ baseURL: API_URL })

const clean = (params = {}) =>
  Object.fromEntries(Object.entries(params).filter(([, v]) => v !== '' && v != null))

export const getEvents = (params) =>
  api.get('/events', { params: clean(params) }).then((r) => r.data)

export const getMachines = () => api.get('/machines').then((r) => r.data)

export const getStats = (minutes = 60) =>
  api.get('/stats', { params: { minutes } }).then((r) => r.data)

export const getActions = () => api.get('/mitigation/actions').then((r) => r.data)

export const getBlocked = () => api.get('/mitigation/blocked').then((r) => r.data)

export const requestAction = (ip, action) =>
  api.post('/mitigation/actions', { ip, action }).then((r) => r.data)