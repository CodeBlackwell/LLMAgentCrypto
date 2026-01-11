import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { formatDistanceToNow, format } from 'date-fns'

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

export default function Backtests() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['backtests'],
    queryFn: () => api.getBacktests({ limit: 50 }),
    refetchInterval: 5000,
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading backtests...</div>
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-600">
        Failed to load backtests: {error.message}
      </div>
    )
  }

  const backtests = data?.backtests || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Backtests</h2>
          <p className="text-gray-500 mt-1">
            {backtests.length} backtest{backtests.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Link to="/backtests/new" className="btn btn-primary">
          New Backtest
        </Link>
      </div>

      {backtests.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">No backtests yet</p>
          <Link to="/backtests/new" className="btn btn-primary">
            Run Your First Backtest
          </Link>
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr className="text-left text-sm text-gray-500">
                <th className="px-6 py-3 font-medium">Strategy</th>
                <th className="px-6 py-3 font-medium">Asset</th>
                <th className="px-6 py-3 font-medium">Date Range</th>
                <th className="px-6 py-3 font-medium">Return</th>
                <th className="px-6 py-3 font-medium">Sharpe</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {backtests.map(backtest => (
                <tr key={backtest.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <Link
                      to={`/backtests/${backtest.id}`}
                      className="text-primary-600 hover:text-primary-700 font-medium"
                    >
                      {backtest.strategy_name}
                    </Link>
                    {backtest.signal_provider && (
                      <p className="text-xs text-gray-400">{backtest.signal_provider}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    <span className="font-mono">{backtest.asset}</span>
                    <p className="text-xs text-gray-400">{backtest.asset_type}</p>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {backtest.start_date && backtest.end_date ? (
                      <>
                        {format(new Date(backtest.start_date), 'MMM d, yyyy')}
                        <br />
                        <span className="text-gray-400">to</span>{' '}
                        {format(new Date(backtest.end_date), 'MMM d, yyyy')}
                      </>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {backtest.total_return != null ? (
                      <span
                        className={`font-medium ${
                          backtest.total_return >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                      >
                        {backtest.total_return >= 0 ? '+' : ''}
                        {backtest.total_return.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-600">
                    {backtest.sharpe_ratio != null
                      ? backtest.sharpe_ratio.toFixed(2)
                      : '-'}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={backtest.status} />
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {backtest.created_at
                      ? formatDistanceToNow(new Date(backtest.created_at), {
                          addSuffix: true,
                        })
                      : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
