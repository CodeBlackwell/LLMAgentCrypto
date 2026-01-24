import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '../api/client'

function Tooltip({ text }) {
  const [isVisible, setIsVisible] = useState(false)

  return (
    <span className="relative inline-block ml-1">
      <button
        type="button"
        className="inline-flex items-center justify-center w-4 h-4 text-xs text-gray-500 bg-gray-200 rounded-full hover:bg-gray-300 focus:outline-none"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
      >
        ?
      </button>
      {isVisible && (
        <div className="absolute z-10 w-48 px-3 py-2 text-sm text-white bg-gray-800 rounded-lg shadow-lg -top-2 left-6">
          {text}
          <div className="absolute w-2 h-2 bg-gray-800 transform rotate-45 top-3 -left-1"></div>
        </div>
      )}
    </span>
  )
}

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
  const [validationErrors, setValidationErrors] = useState({})

  // Validation functions
  const validateField = (name, value, formData = form) => {
    switch (name) {
      case 'strategy_name':
        return !value ? 'Please select a strategy' : ''
      case 'start_date':
      case 'end_date': {
        if (!value) return 'Date is required'
        const start = new Date(name === 'start_date' ? value : formData.start_date)
        const end = new Date(name === 'end_date' ? value : formData.end_date)
        if (name === 'end_date' && end <= start) {
          return 'End date must be after start date'
        }
        const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
        if (daysDiff > 730) {
          return 'Date range cannot exceed 2 years (730 days)'
        }
        return ''
      }
      case 'initial_cash':
        return value < 100 ? 'Initial cash must be at least $100' : ''
      case 'threshold':
        return (value < 0 || value > 1) ? 'Threshold must be between 0 and 1' : ''
      case 'cash_at_risk':
        return (value < 0 || value > 1) ? 'Position size must be between 0 and 1' : ''
      default:
        return ''
    }
  }

  const validateAllFields = () => {
    const errors = {}
    const fieldsToValidate = ['strategy_name', 'start_date', 'end_date', 'initial_cash', 'threshold', 'cash_at_risk']
    fieldsToValidate.forEach(field => {
      const error = validateField(field, form[field], form)
      if (error) errors[field] = error
    })
    return errors
  }

  const handleBlur = (e) => {
    const { name, value, type } = e.target
    const fieldValue = type === 'number' ? parseFloat(value) : value
    const error = validateField(name, fieldValue, form)
    setValidationErrors(prev => ({
      ...prev,
      [name]: error
    }))
    // Also validate related date field when blurring start_date or end_date
    if (name === 'start_date') {
      const endError = validateField('end_date', form.end_date, { ...form, start_date: fieldValue })
      setValidationErrors(prev => ({ ...prev, end_date: endError }))
    } else if (name === 'end_date') {
      const startError = validateField('start_date', form.start_date, { ...form, end_date: fieldValue })
      setValidationErrors(prev => ({ ...prev, start_date: startError }))
    }
  }

  const hasValidationErrors = Object.values(validationErrors).some(error => error !== '')

  // Calculate trading days and estimated duration
  const calculateTradingDays = (startDate, endDate) => {
    if (!startDate || !endDate) return 0
    const start = new Date(startDate)
    const end = new Date(endDate)
    if (end <= start) return 0

    let tradingDays = 0
    const current = new Date(start)
    while (current <= end) {
      const dayOfWeek = current.getDay()
      // Count weekdays only (Monday=1 through Friday=5)
      if (dayOfWeek !== 0 && dayOfWeek !== 6) {
        tradingDays++
      }
      current.setDate(current.getDate() + 1)
    }
    return tradingDays
  }

  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    if (minutes === 0) {
      return `${remainingSeconds}s`
    }
    return `${minutes}m ${remainingSeconds}s`
  }

  const tradingDays = calculateTradingDays(form.start_date, form.end_date)
  const estimatedSeconds = tradingDays * 2  // ~2 seconds per trading day
  const estimatedDuration = formatDuration(estimatedSeconds)

  // Date preset handlers
  const formatDateString = (date) => {
    return date.toISOString().split('T')[0]
  }

  const applyDatePreset = (preset) => {
    const today = new Date()
    const endDate = formatDateString(today)
    let startDate

    switch (preset) {
      case '3months': {
        const start = new Date(today)
        start.setMonth(start.getMonth() - 3)
        startDate = formatDateString(start)
        break
      }
      case '6months': {
        const start = new Date(today)
        start.setMonth(start.getMonth() - 6)
        startDate = formatDateString(start)
        break
      }
      case 'ytd': {
        startDate = `${today.getFullYear()}-01-01`
        break
      }
      case '1year': {
        const start = new Date(today)
        start.setFullYear(start.getFullYear() - 1)
        startDate = formatDateString(start)
        break
      }
      default:
        return
    }

    setForm(prev => ({
      ...prev,
      start_date: startDate,
      end_date: endDate
    }))
    // Clear any date validation errors
    setValidationErrors(prev => ({
      ...prev,
      start_date: '',
      end_date: ''
    }))
  }

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
    const errors = validateAllFields()
    setValidationErrors(errors)
    if (Object.values(errors).some(error => error !== '')) {
      return
    }
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
            onBlur={handleBlur}
            required
            className={`input ${validationErrors.strategy_name ? 'border-red-500' : ''}`}
          >
            <option value="">Select a strategy...</option>
            {strategies?.strategies?.map(s => (
              <option key={s.name} value={s.name}>
                {s.name} - {s.description}
              </option>
            ))}
          </select>
          {validationErrors.strategy_name && (
            <p className="mt-1 text-sm text-red-600">{validationErrors.strategy_name}</p>
          )}
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
              onBlur={handleBlur}
              required
              className={`input ${validationErrors.start_date ? 'border-red-500' : ''}`}
            />
            {validationErrors.start_date && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.start_date}</p>
            )}
          </div>
          <div>
            <label htmlFor="end_date" className="label">End Date</label>
            <input
              id="end_date"
              name="end_date"
              type="date"
              value={form.end_date}
              onChange={handleChange}
              onBlur={handleBlur}
              required
              className={`input ${validationErrors.end_date ? 'border-red-500' : ''}`}
            />
            {validationErrors.end_date && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.end_date}</p>
            )}
          </div>
        </div>

        {/* Date Presets */}
        <div className="flex flex-wrap gap-2">
          <span className="text-sm text-gray-500 mr-2 self-center">Quick select:</span>
          <button
            type="button"
            onClick={() => applyDatePreset('3months')}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
          >
            Last 3 months
          </button>
          <button
            type="button"
            onClick={() => applyDatePreset('6months')}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
          >
            Last 6 months
          </button>
          <button
            type="button"
            onClick={() => applyDatePreset('ytd')}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
          >
            YTD
          </button>
          <button
            type="button"
            onClick={() => applyDatePreset('1year')}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
          >
            Last year
          </button>
        </div>

        {/* Estimated Duration */}
        {tradingDays > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-blue-800 font-medium">
                Estimated duration: {estimatedDuration} ({tradingDays} trading days)
              </span>
            </div>
          </div>
        )}

        {/* Trading Parameters */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label htmlFor="initial_cash" className="label">
              Initial Cash ($)
              <Tooltip text="Starting capital for the backtest simulation" />
            </label>
            <input
              id="initial_cash"
              name="initial_cash"
              type="number"
              min="0"
              step="1000"
              value={form.initial_cash}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`input ${validationErrors.initial_cash ? 'border-red-500' : ''}`}
            />
            {validationErrors.initial_cash && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.initial_cash}</p>
            )}
          </div>
          <div>
            <label htmlFor="threshold" className="label">
              Threshold
              <Tooltip text="Minimum confidence score (0-1) required to execute a trade" />
            </label>
            <input
              id="threshold"
              name="threshold"
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={form.threshold}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`input ${validationErrors.threshold ? 'border-red-500' : ''}`}
            />
            {validationErrors.threshold && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.threshold}</p>
            )}
          </div>
          <div>
            <label htmlFor="cash_at_risk" className="label">
              Position Size
              <Tooltip text="Fraction of available cash to use per trade (0.25 = 25%)" />
            </label>
            <input
              id="cash_at_risk"
              name="cash_at_risk"
              type="number"
              min="0"
              max="1"
              step="0.05"
              value={form.cash_at_risk}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`input ${validationErrors.cash_at_risk ? 'border-red-500' : ''}`}
            />
            {validationErrors.cash_at_risk && (
              <p className="mt-1 text-sm text-red-600">{validationErrors.cash_at_risk}</p>
            )}
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
            disabled={createMutation.isPending || hasValidationErrors}
            className={`btn btn-primary flex-1 ${hasValidationErrors ? 'opacity-50 cursor-not-allowed' : ''}`}
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
