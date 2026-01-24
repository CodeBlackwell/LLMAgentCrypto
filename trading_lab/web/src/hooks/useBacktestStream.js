import { useState, useEffect, useRef, useCallback } from 'react'

const API_BASE = '/api'

/**
 * React hook for consuming SSE stream of backtest updates.
 *
 * @param {string} backtestId - The backtest ID to stream updates for
 * @param {boolean} enabled - Whether the stream should be active
 * @returns {{ data: object|null, error: string|null, isConnected: boolean }}
 */
export function useBacktestStream(backtestId, enabled = true) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [isConnected, setIsConnected] = useState(false)

  const eventSourceRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptRef = useRef(0)

  // Calculate reconnection delay with exponential backoff
  // 1s, 2s, 4s, 8s, max 30s
  const getReconnectDelay = useCallback(() => {
    const baseDelay = 1000
    const maxDelay = 30000
    const delay = Math.min(baseDelay * Math.pow(2, reconnectAttemptRef.current), maxDelay)
    return delay
  }, [])

  const connect = useCallback(() => {
    if (!backtestId || !enabled) {
      return
    }

    // Close existing connection if any
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    const url = `${API_BASE}/backtests/${backtestId}/stream`
    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      setIsConnected(true)
      setError(null)
      reconnectAttemptRef.current = 0
    }

    eventSource.onerror = () => {
      setIsConnected(false)
      eventSource.close()

      // Don't reconnect if disabled
      if (!enabled) {
        return
      }

      // Schedule reconnection with exponential backoff
      const delay = getReconnectDelay()
      reconnectAttemptRef.current += 1

      reconnectTimeoutRef.current = setTimeout(() => {
        connect()
      }, delay)
    }

    // Handle progress events
    eventSource.addEventListener('progress', (event) => {
      try {
        const parsed = JSON.parse(event.data)
        setData((prev) => ({
          ...prev,
          ...parsed,
        }))
      } catch {
        // Ignore parse errors
      }
    })

    // Handle trades events
    eventSource.addEventListener('trades', (event) => {
      try {
        const parsed = JSON.parse(event.data)
        setData((prev) => ({
          ...prev,
          trades: parsed.trades || [],
        }))
      } catch {
        // Ignore parse errors
      }
    })

    // Handle complete events
    eventSource.addEventListener('complete', (event) => {
      try {
        const parsed = JSON.parse(event.data)
        setData((prev) => ({
          ...prev,
          ...parsed,
          status: 'completed',
        }))
      } catch {
        // Ignore parse errors
      }
      // Connection will be closed by server on terminal state
      setIsConnected(false)
    })

    // Handle error events
    eventSource.addEventListener('error', (event) => {
      try {
        const parsed = JSON.parse(event.data)
        setData((prev) => ({
          ...prev,
          ...parsed,
          status: 'failed',
        }))
        setError(parsed.error_message || 'Backtest failed')
      } catch {
        // Ignore parse errors
      }
      // Connection will be closed by server on terminal state
      setIsConnected(false)
    })
  }, [backtestId, enabled, getReconnectDelay])

  // Connect/disconnect based on enabled state
  useEffect(() => {
    if (enabled && backtestId) {
      connect()
    }

    return () => {
      // Cleanup on unmount or when disabled
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      setIsConnected(false)
    }
  }, [backtestId, enabled, connect])

  return { data, error, isConnected }
}
