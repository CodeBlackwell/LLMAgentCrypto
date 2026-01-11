const API_BASE = '/api'

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  // Strategies
  getStrategies: () => request('/strategies'),
  getStrategy: (name) => request(`/strategies/${name}`),

  // Backtests
  getBacktests: (params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`/backtests${query ? `?${query}` : ''}`)
  },
  getBacktest: (id) => request(`/backtests/${id}`),
  createBacktest: (data) => request('/backtests', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  deleteBacktest: (id) => request(`/backtests/${id}`, { method: 'DELETE' }),
  cancelBacktest: (id) => request(`/backtests/${id}/cancel`, { method: 'POST' }),

  // Results
  getBacktestResults: (id) => request(`/results/${id}`),
  getBacktestTrades: (id, params = {}) => {
    const query = new URLSearchParams(params).toString()
    return request(`/results/${id}/trades${query ? `?${query}` : ''}`)
  },
  compareBacktests: (ids) => request('/results/compare', {
    method: 'POST',
    body: JSON.stringify({ backtest_ids: ids }),
  }),
}
