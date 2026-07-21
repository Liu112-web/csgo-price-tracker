import axios from 'axios'

// Vite 代理会把 /api 转发到后端 127.0.0.1:8765
const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

export const api = {
  getConfig: () => http.get('/config').then(r => r.data),
  updateConfig: (cfg) => http.post('/config', cfg).then(r => r.data),
  getLatest: () => http.get('/price/latest').then(r => r.data),
  getDaily: () => http.get('/price/daily').then(r => r.data),
  getHistory: () => http.get('/price/history').then(r => r.data),
  getAlerts: () => http.get('/alerts').then(r => r.data),
  triggerCheck: () => http.post('/check/now').then(r => r.data),
}

export default http
