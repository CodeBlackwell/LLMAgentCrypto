import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
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
  const navigate = useNavigate()
  const [selectedIds, setSelectedIds] = useState([])
  const [statusFilter, setStatusFilter] = useState('all')

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['backtests'],
    queryFn: () => api.getBacktests({ limit: 50 }),
    refetchInterval: 5000,
  })

  const handleToggleSelect = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  const handleSelectAll = (filteredBacktests) => {
    const filteredIds = filteredBacktests.map((b) => b.id)
    const allSelected = filteredIds.every((id) => selectedIds.includes(id))
    if (allSelected) {
      setSelectedIds((prev) => prev.filter((id) => !filteredIds.includes(id)))
    } else {
      setSelectedIds((prev) => [...new Set([...prev, ...filteredIds])])
    }
  }

  const handleCompareSelected = () => {
    if (selectedIds.length >= 2 && selectedIds.length <= 10) {
      navigate(`/backtests/compare?ids=${selectedIds.join(',')}`)
    }
  }

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

  const filteredBacktests =
    statusFilter === 'all'
      ? backtests
      : backtests.filter((b) => b.status === statusFilter)

  const isCompareDisabled = selectedIds.length < 2 || selectedIds.length > 10

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Backtests</h2>
          <p className="text-gray-500 mt-1">
            {backtests.length} backtest{backtests.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleCompareSelected}
            disabled={isCompareDisabled}
            className={`btn ${
              isCompareDisabled
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'btn-secondary'
            }`}
          >
            Compare Selected ({selectedIds.length})
          </button>
          <Link to="/backtests/new" className="btn btn-primary">
            New Backtest
          </Link>
        </div>
      </div>

      {/* Status Filter Bar */}
      <div className="flex items-center gap-4 bg-gray-50 p-4 rounded-lg">
        <label htmlFor="status-filter" className="text-sm font-medium text-gray-700">
          Filter by Status:
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm"
        >
          <option value="all">All</option>
          <option value="running">Running</option>
          <option value="pending">Pending</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
        {statusFilter !== 'all' && (
          <span className="text-sm text-gray-500">
            Showing {filteredBacktests.length} of {backtests.length} backtests
          </span>
        )}
      </div>

      {filteredBacktests.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">
            {backtests.length === 0
              ? 'No backtests yet'
              : `No backtests with status "${statusFilter}"`}
          </p>
          {backtests.length === 0 && (
            <Link to="/backtests/new" className="btn btn-primary">
              Run Your First Backtest
            </Link>
          )}
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr className="text-left text-sm text-gray-500">
                <th className="px-6 py-3 font-medium">
                  <input
                    type="checkbox"
                    checked={
                      filteredBacktests.length > 0 &&
                      filteredBacktests.every((b) => selectedIds.includes(b.id))
                    }
                    onChange={() => handleSelectAll(filteredBacktests)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </th>
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
              {filteredBacktests.map((backtest) => (
                <tr key={backtest.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(backtest.id)}
                      onChange={() => handleToggleSelect(backtest.id)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                  </td>
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
