import axios from 'axios'

// Клиент к серверу приложения. withCredentials — куки сессии (Flask-Login).
const client = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

export default client

export const api = {
  // Аутентификация
  login: (login, password) => client.post('/auth/login', { login, password }),
  logout: () => client.post('/auth/logout'),
  me: () => client.get('/auth/me'),

  // Игроки и рейтинги
  players: () => client.get('/players'),
  player: (id) => client.get(`/players/${id}`),
  teamRatings: () => client.get('/ratings/team'),
  setModifiers: (id, mods) => client.post(`/ratings/player/${id}/modifiers`, mods),

  // Сценарии поддержки решений
  lineupSuggestion: () => client.get('/lineup/suggestion'),
  approveLineup: (payload) => client.post('/lineup/approve', payload),
  recommendations: (id) => client.get(`/recommendations/player/${id}`),
  alerts: () => client.get('/alerts/feed'),

  // Ввод данных
  addRaw: (payload) => client.post('/data/raw', payload),
  dataSchema: () => client.get('/data/schema'),
  addRawBatch: (payload) => client.post('/data/raw/batch', payload),
  importPreview: (csv) => client.post('/data/import/preview', csv, {
    headers: { 'Content-Type': 'text/csv' },
  }),
}
