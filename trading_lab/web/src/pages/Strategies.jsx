import { useQuery, useMutation } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

function StrategyCard({ strategy }) {
  const navigate = useNavigate()

  const quickRunMutation = useMutation({
    mutationFn: () => api.createBacktest({
      strategy_name: strategy.name,
      signal_provider: strategy.default_provider,
      asset: 'BTC/USD',
      asset_type: 'crypto',
      start_date: '2024-01-01',
      end_date: '2024-06-30',
      initial_cash: 100000,
      threshold: 0.7,
      cash_at_risk: 0.25,
      exchange: 'kraken',
    }),
    onSuccess: (data) => {
      navigate(`/backtests/${data.backtest_id}`)
    },
  })

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">{strategy.name}</h3>
          <p className="text-sm text-gray-500 mt-1">{strategy.description}</p>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {strategy.asset_types.map(type => (
          <span
            key={type}
            className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs"
          >
            {type}
          </span>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t flex items-center justify-between">
        <span className="text-xs text-gray-400">
          Provider: {strategy.default_provider}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => quickRunMutation.mutate()}
            disabled={quickRunMutation.isPending}
            className="btn btn-secondary text-sm"
          >
            {quickRunMutation.isPending ? 'Running...' : 'Quick Run'}
          </button>
          <Link
            to={`/backtests/new?strategy=${strategy.name}`}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            Run Backtest
          </Link>
        </div>
      </div>
    </div>
  )
}

export default function Strategies() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['strategies'],
    queryFn: api.getStrategies,
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading strategies...</div>
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        Failed to load strategies: {error.message}
      </div>
    )
  }

  const strategies = data?.strategies || []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Strategies</h2>
        <p className="text-gray-500 mt-1">
          Available trading strategies for backtesting
        </p>
      </div>

      {strategies.length === 0 ? (
        <div className="card text-center py-8">
          <p className="text-gray-500">No strategies registered</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {strategies.map(strategy => (
            <StrategyCard key={strategy.name} strategy={strategy} />
          ))}
        </div>
      )}
    </div>
  )
}
