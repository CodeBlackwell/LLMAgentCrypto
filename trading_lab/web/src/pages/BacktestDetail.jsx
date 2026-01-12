import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { format } from 'date-fns'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function StatusBadge({ status }) {
  const colors = {
    completed: 'bg-green-100 text-green-800',
    running: 'bg-blue-100 text-blue-800',
    pending: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  }

  return (
    <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[status] || colors.pending}`}>
      {status}
    </span>
  )
}

function MetricCard({ label, value, subtext, positive }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-xl font-bold mt-1 ${
        positive === true ? 'text-green-600' :
        positive === false ? 'text-red-600' :
        'text-gray-900'
      }`}>
        {value}
      </p>
      {subtext && <p className="text-xs text-gray-400 mt-1">{subtext}</p>}
    </div>
  )
}

export default function BacktestDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: backtest, isLoading, error } = useQuery({
    queryKey: ['backtest', id],
    queryFn: () => api.getBacktest(id),
    refetchInterval: (data) => {
      return data?.status === 'running' || data?.status === 'pending' ? 2000 : false
    },
  })

  const { data: results } = useQuery({
    queryKey: ['backtest-results', id],
    queryFn: () => api.getBacktestResults(id),
    enabled: backtest?.status === 'completed',
  })

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteBacktest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backtests'] })
      navigate('/backtests')
    },
  })

  const cancelMutation = useMutation({
    mutationFn: () => api.cancelBacktest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['backtest', id] })
    },
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading backtest...</div>
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        Failed to load backtest: {error.message}
      </div>
    )
  }

  const isRunning = backtest.status === 'running' || backtest.status === 'pending'
  const dailyStats = results?.daily_stats || []
  const trades = results?.trades || []

  // Prepare chart data
  const chartData = dailyStats.map(stat => ({
    date: format(new Date(stat.date), 'MMM d'),
    value: stat.portfolio_value,
    return: stat.cumulative_return,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold text-gray-900">
              {backtest.strategy_name}
            </h2>
            <StatusBadge status={backtest.status} />
          </div>
          <p className="text-gray-500 mt-1">
            {backtest.asset} on {backtest.exchange || 'default exchange'}
          </p>
        </div>
        <div className="flex gap-2">
          {isRunning && (
            <button
              onClick={() => cancelMutation.mutate()}
              disabled={cancelMutation.isPending}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          )}
          <button
            onClick={() => navigate(`/backtests/new?clone=${id}`)}
            className="btn btn-secondary"
          >
            Clone & Edit
          </button>
          <button
            onClick={() => {
              if (confirm('Delete this backtest?')) {
                deleteMutation.mutate()
              }
            }}
            disabled={deleteMutation.isPending}
            className="btn bg-red-100 text-red-700 hover:bg-red-200"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Metrics */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Performance Metrics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Initial Cash"
            value={`$${backtest.initial_cash?.toLocaleString() || 0}`}
          />
          <MetricCard
            label="Final Value"
            value={`$${backtest.final_value?.toLocaleString() || '-'}`}
          />
          <MetricCard
            label="Total Return"
            value={backtest.total_return != null ? `${backtest.total_return.toFixed(2)}%` : '-'}
            positive={backtest.total_return != null ? backtest.total_return >= 0 : undefined}
          />
          <MetricCard
            label="Win Rate"
            value={backtest.win_rate != null ? `${(backtest.win_rate * 100).toFixed(1)}%` : '-'}
          />
          <MetricCard
            label="Sharpe Ratio"
            value={backtest.sharpe_ratio?.toFixed(2) || '-'}
          />
          <MetricCard
            label="Max Drawdown"
            value={backtest.max_drawdown != null ? `${(backtest.max_drawdown * 100).toFixed(2)}%` : '-'}
            positive={backtest.max_drawdown != null ? false : undefined}
          />
          <MetricCard
            label="Total Trades"
            value={backtest.total_trades || trades.length || '-'}
          />
          <MetricCard
            label="Date Range"
            value={backtest.start_date && backtest.end_date
              ? `${format(new Date(backtest.start_date), 'MMM yyyy')} - ${format(new Date(backtest.end_date), 'MMM yyyy')}`
              : '-'}
          />
        </div>
      </div>

      {/* Equity Curve */}
      {chartData.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Equity Curve</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(val) => [`$${val.toLocaleString()}`, 'Portfolio Value']}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#0ea5e9"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Trades Table */}
      {trades.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900">Trades</h3>
            <span className="text-sm text-gray-500">{trades.length} trades</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-2 font-medium">Time</th>
                  <th className="pb-2 font-medium">Side</th>
                  <th className="pb-2 font-medium">Quantity</th>
                  <th className="pb-2 font-medium">Price</th>
                  <th className="pb-2 font-medium">Total</th>
                  <th className="pb-2 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {trades.slice(0, 20).map(trade => (
                  <tr key={trade.id} className="text-gray-600">
                    <td className="py-2">
                      {trade.timestamp
                        ? format(new Date(trade.timestamp), 'MMM d, yyyy HH:mm')
                        : '-'}
                    </td>
                    <td className="py-2">
                      <span className={trade.side === 'buy' ? 'text-green-600' : 'text-red-600'}>
                        {trade.side.toUpperCase()}
                      </span>
                    </td>
                    <td className="py-2">{trade.quantity?.toFixed(6)}</td>
                    <td className="py-2">${trade.price?.toLocaleString()}</td>
                    <td className="py-2">${trade.total_value?.toLocaleString()}</td>
                    <td className="py-2">
                      {trade.signal_confidence != null
                        ? `${(trade.signal_confidence * 100).toFixed(1)}%`
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {trades.length > 20 && (
              <p className="text-center text-sm text-gray-400 mt-4">
                Showing 20 of {trades.length} trades
              </p>
            )}
          </div>
        </div>
      )}

      {/* Back Link */}
      <div className="pt-4">
        <Link to="/backtests" className="text-primary-600 hover:text-primary-700">
          &larr; Back to Backtests
        </Link>
      </div>
    </div>
  )
}
