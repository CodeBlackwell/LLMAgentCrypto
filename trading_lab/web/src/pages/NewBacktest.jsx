import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '../api/client'

export default function NewBacktest() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const cloneId = searchParams.get('clone')

  const [form, setForm] = useState({
    strategy_name: searchParams.get('strategy') || '',
    signal_provider: 'random',
    asset: 'BTC/USD',
    asset_type: 'crypto',
    start_date: '2024-01-01',
    end_date: '2024-06-30',
    initial_cash: 100000,
    threshold: 0.7,
    cash_at_risk: 0.25,
    exchange: 'kraken',
  })

  const [error, setError] = useState(null)

  const { data: strategies } = useQuery({
    queryKey: ['strategies'],
    queryFn: api.getStrategies,
  })

  const { data: clonedBacktest } = useQuery({
    queryKey: ['backtest', cloneId],
    queryFn: () => api.getBacktest(cloneId),
    enabled: !!cloneId,
  })

  useEffect(() => {
    if (clonedBacktest) {
      setForm({
        strategy_name: clonedBacktest.strategy_name || '',
        signal_provider: clonedBacktest.signal_provider || 'random',
        asset: clonedBacktest.asset || 'BTC/USD',
        asset_type: clonedBacktest.asset_type || 'crypto',
        start_date: clonedBacktest.start_date || '2024-01-01',
        end_date: clonedBacktest.end_date || '2024-06-30',
        initial_cash: clonedBacktest.initial_cash || 100000,
        threshold: clonedBacktest.threshold || 0.7,
        cash_at_risk: clonedBacktest.cash_at_risk || 0.25,
        exchange: clonedBacktest.exchange || 'kraken',
      })
    }
  }, [clonedBacktest])

  const createMutation = useMutation({
    mutationFn: api.createBacktest,
    onSuccess: (data) => {
      navigate(`/backtests/${data.backtest_id}`)
    },
    onError: (err) => {
      setError(err.message)
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    setError(null)
    createMutation.mutate(form)
  }

  const handleChange = (e) => {
    const { name, value, type } = e.target
    setForm(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value,
    }))
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">New Backtest</h2>
        <p className="text-gray-500 mt-1">Configure and run a strategy backtest</p>
        {cloneId && (
          <p className="text-blue-600 mt-2 text-sm">
            Cloning from Backtest #{cloneId}
          </p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="card space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {/* Strategy Selection */}
        <div>
          <label htmlFor="strategy_name" className="label">Strategy</label>
          <select
            id="strategy_name"
            name="strategy_name"
            value={form.strategy_name}
            onChange={handleChange}
            required
            className="input"
          >
            <option value="">Select a strategy...</option>
            {strategies?.strategies?.map(s => (
              <option key={s.name} value={s.name}>
                {s.name} - {s.description}
              </option>
            ))}
          </select>
        </div>

        {/* Asset Configuration */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="asset" className="label">Asset</label>
            <input
              id="asset"
              name="asset"
              type="text"
              value={form.asset}
              onChange={handleChange}
              placeholder="BTC/USD"
              required
              className="input"
            />
          </div>
          <div>
            <label htmlFor="asset_type" className="label">Asset Type</label>
            <select
              id="asset_type"
              name="asset_type"
              value={form.asset_type}
              onChange={handleChange}
              className="input"
            >
              <option value="crypto">Crypto</option>
              <option value="stock">Stock</option>
              <option value="forex">Forex</option>
            </select>
          </div>
        </div>

        {/* Date Range */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="start_date" className="label">Start Date</label>
            <input
              id="start_date"
              name="start_date"
              type="date"
              value={form.start_date}
              onChange={handleChange}
              required
              className="input"
            />
          </div>
          <div>
            <label htmlFor="end_date" className="label">End Date</label>
            <input
              id="end_date"
              name="end_date"
              type="date"
              value={form.end_date}
              onChange={handleChange}
              required
              className="input"
            />
          </div>
        </div>

        {/* Trading Parameters */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label htmlFor="initial_cash" className="label">Initial Cash ($)</label>
            <input
              id="initial_cash"
              name="initial_cash"
              type="number"
              min="0"
              step="1000"
              value={form.initial_cash}
              onChange={handleChange}
              className="input"
            />
          </div>
          <div>
            <label htmlFor="threshold" className="label">Threshold</label>
            <input
              id="threshold"
              name="threshold"
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={form.threshold}
              onChange={handleChange}
              className="input"
            />
          </div>
          <div>
            <label htmlFor="cash_at_risk" className="label">Position Size</label>
            <input
              id="cash_at_risk"
              name="cash_at_risk"
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={form.cash_at_risk}
              onChange={handleChange}
              className="input"
            />
          </div>
        </div>

        {/* Exchange */}
        {form.asset_type === 'crypto' && (
          <div>
            <label htmlFor="exchange" className="label">Exchange</label>
            <select
              id="exchange"
              name="exchange"
              value={form.exchange}
              onChange={handleChange}
              className="input"
            >
              <option value="kraken">Kraken</option>
              <option value="coinbase">Coinbase</option>
              <option value="binance">Binance</option>
              <option value="bitfinex">Bitfinex</option>
            </select>
          </div>
        )}

        {/* Submit */}
        <div className="flex gap-4 pt-4">
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="btn btn-primary flex-1"
          >
            {createMutation.isPending ? 'Starting...' : 'Start Backtest'}
          </button>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="btn btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
