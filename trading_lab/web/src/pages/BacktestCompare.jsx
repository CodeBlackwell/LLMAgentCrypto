import { useSearchParams, Link } from 'react-router-dom'
import { useQuery, useQueries } from '@tanstack/react-query'
import { api } from '../api/client'
import { format } from 'date-fns'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const CHART_COLORS = [
  '#0ea5e9', // sky-500
  '#f97316', // orange-500
  '#8b5cf6', // violet-500
  '#10b981', // emerald-500
  '#f43f5e', // rose-500
  '#6366f1', // indigo-500
]

function findBestValue(backtests, key, mode = 'highest') {
  const values = backtests.map(b => b[key]).filter(v => v != null)
  if (values.length === 0) return null

  if (mode === 'highest') {
    return Math.max(...values)
  } else {
    // For drawdown, we want the value closest to 0 (least negative)
    return values.reduce((best, val) =>
      Math.abs(val) < Math.abs(best) ? val : best
    , values[0])
  }
}

function MetricRow({ label, backtests, metricKey, formatter, mode = 'highest' }) {
  const bestValue = findBestValue(backtests, metricKey, mode)

  return (
    <tr className="border-b">
      <td className="px-4 py-3 font-medium text-gray-700">{label}</td>
      {backtests.map(backtest => {
        const value = backtest[metricKey]
        const isBest = value != null && (
          mode === 'highest'
            ? value === bestValue
            : Math.abs(value) === Math.abs(bestValue)
        )

        return (
          <td
            key={backtest.id}
            className={`px-4 py-3 text-center ${isBest ? 'text-green-600 font-bold' : 'text-gray-600'}`}
          >
            {value != null ? formatter(value) : '-'}
          </td>
        )
      })}
    </tr>
  )
}

export default function BacktestCompare() {
  const [searchParams] = useSearchParams()
  const idsParam = searchParams.get('ids') || ''
  const ids = idsParam.split(',').filter(id => id.trim()).map(id => parseInt(id.trim(), 10)).filter(id => !isNaN(id))

  const { data, isLoading, error } = useQuery({
    queryKey: ['compare-backtests', ids.join(',')],
    queryFn: () => api.compareBacktests(ids),
    enabled: ids.length >= 2,
  })

  // Fetch results for each backtest to get equity curves
  const resultsQueries = useQueries({
    queries: ids.map(id => ({
      queryKey: ['backtest-results', id],
      queryFn: () => api.getBacktestResults(id),
      enabled: ids.length >= 2 && !!data?.backtests,
    })),
  })

  // Validation error
  if (ids.length < 2) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Compare Backtests</h2>
        </div>
        <div className="card text-center py-12">
          <p className="text-red-600 mb-4">
            Please select at least 2 backtests to compare.
            {ids.length === 1 && ' Only 1 backtest ID provided.'}
            {ids.length === 0 && ' No valid backtest IDs provided.'}
          </p>
          <p className="text-gray-500 text-sm mb-4">
            Use URL parameter: ?ids=1,2,3
          </p>
          <Link to="/backtests" className="btn btn-primary">
            Back to Backtests
          </Link>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <p className="mt-2 text-gray-500">Loading comparison data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Compare Backtests</h2>
        </div>
        <div className="card text-center py-12">
          <p className="text-red-600 mb-4">
            Failed to load comparison: {error.message}
          </p>
          <Link to="/backtests" className="btn btn-primary">
            Back to Backtests
          </Link>
        </div>
      </div>
    )
  }

  const backtests = data?.backtests || []

  if (backtests.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-900">Compare Backtests</h2>
        </div>
        <div className="card text-center py-12">
          <p className="text-red-600 mb-4">No backtests found with the provided IDs.</p>
          <Link to="/backtests" className="btn btn-primary">
            Back to Backtests
          </Link>
        </div>
      </div>
    )
  }

  // Prepare equity curve data for overlay chart
  const allResultsLoaded = resultsQueries.every(q => q.isSuccess || q.isError)
  let chartData = []

  if (allResultsLoaded) {
    // Collect all dates and create a unified timeline
    const dateMap = new Map()

    resultsQueries.forEach((query, index) => {
      if (query.data?.daily_stats) {
        const backtest = backtests[index]
        query.data.daily_stats.forEach(stat => {
          const dateKey = stat.date
          if (!dateMap.has(dateKey)) {
            dateMap.set(dateKey, { date: dateKey })
          }
          dateMap.get(dateKey)[`backtest_${backtest.id}`] = stat.portfolio_value
        })
      }
    })

    chartData = Array.from(dateMap.values())
      .sort((a, b) => new Date(a.date) - new Date(b.date))
      .map(item => ({
        ...item,
        dateLabel: format(new Date(item.date), 'MMM d'),
      }))
  }

  const strategyNames = backtests.map(b => b.strategy_name).join(' vs ')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Compare Backtests</h2>
          <p className="text-gray-500 mt-1">{strategyNames}</p>
        </div>
        <Link to="/backtests" className="btn btn-secondary">
          Back to Backtests
        </Link>
      </div>

      {/* Backtest Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {backtests.map((backtest, index) => (
          <div
            key={backtest.id}
            className="card"
            style={{ borderLeft: `4px solid ${CHART_COLORS[index % CHART_COLORS.length]}` }}
          >
            <div className="flex items-center justify-between mb-2">
              <Link
                to={`/backtests/${backtest.id}`}
                className="font-semibold text-primary-600 hover:text-primary-700"
              >
                {backtest.strategy_name}
              </Link>
              <span className="text-xs text-gray-400">ID: {backtest.id}</span>
            </div>
            <p className="text-sm text-gray-500">{backtest.asset}</p>
            <p className="text-sm text-gray-500">
              Initial: ${backtest.initial_cash?.toLocaleString() || '-'}
            </p>
          </div>
        ))}
      </div>

      {/* Metrics Comparison Table */}
      <div className="card overflow-hidden p-0">
        <div className="px-6 py-4 border-b bg-gray-50">
          <h3 className="font-semibold text-gray-900">Metrics Comparison</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr className="text-left text-sm text-gray-500 border-b">
                <th className="px-4 py-3 font-medium">Metric</th>
                {backtests.map((backtest, index) => (
                  <th
                    key={backtest.id}
                    className="px-4 py-3 font-medium text-center"
                    style={{ borderTop: `3px solid ${CHART_COLORS[index % CHART_COLORS.length]}` }}
                  >
                    {backtest.strategy_name}
                    <div className="text-xs text-gray-400 font-normal">{backtest.asset}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <MetricRow
                label="Total Return"
                backtests={backtests}
                metricKey="total_return"
                formatter={(v) => `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`}
                mode="highest"
              />
              <MetricRow
                label="Sharpe Ratio"
                backtests={backtests}
                metricKey="sharpe_ratio"
                formatter={(v) => v.toFixed(2)}
                mode="highest"
              />
              <MetricRow
                label="Max Drawdown"
                backtests={backtests}
                metricKey="max_drawdown"
                formatter={(v) => `${(v * 100).toFixed(2)}%`}
                mode="lowest"
              />
              <MetricRow
                label="Win Rate"
                backtests={backtests}
                metricKey="win_rate"
                formatter={(v) => `${(v * 100).toFixed(1)}%`}
                mode="highest"
              />
              <MetricRow
                label="Total Trades"
                backtests={backtests}
                metricKey="total_trades"
                formatter={(v) => v.toString()}
                mode="highest"
              />
              <tr className="border-b bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-700">Final Value</td>
                {backtests.map(backtest => {
                  const bestFinal = findBestValue(backtests, 'final_value', 'highest')
                  const isBest = backtest.final_value === bestFinal
                  return (
                    <td
                      key={backtest.id}
                      className={`px-4 py-3 text-center ${isBest ? 'text-green-600 font-bold' : 'text-gray-600'}`}
                    >
                      {backtest.final_value != null
                        ? `$${backtest.final_value.toLocaleString()}`
                        : '-'}
                    </td>
                  )
                })}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Equity Curves Overlay Chart */}
      {chartData.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Equity Curves Comparison</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="dateLabel"
                  tick={{ fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  formatter={(val, name) => {
                    const backtestId = name.replace('backtest_', '')
                    const backtest = backtests.find(b => b.id.toString() === backtestId)
                    return [`$${val?.toLocaleString() || '-'}`, backtest?.strategy_name || name]
                  }}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Legend
                  formatter={(value) => {
                    const backtestId = value.replace('backtest_', '')
                    const backtest = backtests.find(b => b.id.toString() === backtestId)
                    return backtest?.strategy_name || value
                  }}
                />
                {backtests.map((backtest, index) => (
                  <Line
                    key={backtest.id}
                    type="monotone"
                    dataKey={`backtest_${backtest.id}`}
                    stroke={CHART_COLORS[index % CHART_COLORS.length]}
                    strokeWidth={2}
                    dot={false}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Loading indicator for equity curves */}
      {!allResultsLoaded && ids.length >= 2 && (
        <div className="card text-center py-8">
          <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-gray-500 text-sm">Loading equity curves...</p>
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
