import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { formatDistanceToNow } from 'date-fns'

function StatusBadge({ status }) {
  const colors = {
    completed: 'bg-green-100 text-green-800',
    running: 'bg-blue-100 text-blue-800',
    pending: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  }

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] || colors.pending}`}>
      {status}
    </span>
  )
}

function StatCard({ label, value, subtext }) {
  return (
    <div className="card">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
      {subtext && <p className="text-xs text-gray-400 mt-1">{subtext}</p>}
    </div>
  )
}

export default function Dashboard() {
  const { data: backtests, isLoading } = useQuery({
    queryKey: ['backtests'],
    queryFn: () => api.getBacktests({ limit: 10 }),
    refetchInterval: 5000, // Poll for updates
  })

  const { data: strategies } = useQuery({
    queryKey: ['strategies'],
    queryFn: api.getStrategies,
  })

  const recentBacktests = backtests?.backtests || []
  const completedCount = recentBacktests.filter(b => b.status === 'completed').length
  const runningCount = recentBacktests.filter(b => b.status === 'running').length

  // Calculate average return
  const avgReturn = recentBacktests
    .filter(b => b.total_return != null)
    .reduce((acc, b, _, arr) => acc + b.total_return / arr.length, 0)

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="text-gray-500 mt-1">Overview of your algorithmic trading lab</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Strategies"
          value={strategies?.strategies?.length || 0}
        />
        <StatCard
          label="Completed Backtests"
          value={completedCount}
        />
        <StatCard
          label="Running"
          value={runningCount}
        />
        <StatCard
          label="Avg Return"
          value={`${avgReturn.toFixed(2)}%`}
          subtext="Last 10 backtests"
        />
      </div>

      {/* Recent Backtests */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Recent Backtests</h3>
          <Link to="/backtests" className="text-primary-600 hover:text-primary-700 text-sm">
            View all
          </Link>
        </div>

        {isLoading ? (
          <p className="text-gray-500">Loading...</p>
        ) : recentBacktests.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No backtests yet</p>
            <Link to="/backtests/new" className="btn btn-primary">
              Run Your First Backtest
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-gray-500 border-b">
                  <th className="pb-3 font-medium">Strategy</th>
                  <th className="pb-3 font-medium">Asset</th>
                  <th className="pb-3 font-medium">Return</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {recentBacktests.map(backtest => (
                  <tr key={backtest.id} className="hover:bg-gray-50">
                    <td className="py-3">
                      <Link
                        to={`/backtests/${backtest.id}`}
                        className="text-primary-600 hover:text-primary-700 font-medium"
                      >
                        {backtest.strategy_name}
                      </Link>
                    </td>
                    <td className="py-3 text-gray-600">{backtest.asset}</td>
                    <td className="py-3">
                      {backtest.total_return != null ? (
                        <span className={backtest.total_return >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {backtest.total_return >= 0 ? '+' : ''}{backtest.total_return.toFixed(2)}%
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="py-3">
                      <StatusBadge status={backtest.status} />
                    </td>
                    <td className="py-3 text-gray-500 text-sm">
                      {backtest.created_at
                        ? formatDistanceToNow(new Date(backtest.created_at), { addSuffix: true })
                        : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/backtests/new" className="card hover:shadow-lg transition-shadow cursor-pointer">
          <h4 className="font-semibold text-gray-900">New Backtest</h4>
          <p className="text-sm text-gray-500 mt-1">Test a strategy against historical data</p>
        </Link>
        <Link to="/strategies" className="card hover:shadow-lg transition-shadow cursor-pointer">
          <h4 className="font-semibold text-gray-900">View Strategies</h4>
          <p className="text-sm text-gray-500 mt-1">Browse available trading strategies</p>
        </Link>
        <Link to="/backtests" className="card hover:shadow-lg transition-shadow cursor-pointer">
          <h4 className="font-semibold text-gray-900">Compare Results</h4>
          <p className="text-sm text-gray-500 mt-1">Analyze and compare backtest performance</p>
        </Link>
      </div>
    </div>
  )
}
