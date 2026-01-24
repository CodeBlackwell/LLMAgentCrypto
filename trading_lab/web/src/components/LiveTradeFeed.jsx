import { useRef, useEffect } from 'react';

export default function LiveTradeFeed({ trades = [] }) {
  const containerRef = useRef(null);

  // Auto-scroll to bottom when new trades arrive
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [trades]);

  // Get last 10 trades
  const recentTrades = trades.slice(-10);

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '--:--:--';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatPrice = (price) => {
    if (price == null) return '-.--';
    return parseFloat(price).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  };

  const formatQuantity = (quantity) => {
    if (quantity == null) return '-';
    return parseFloat(quantity).toFixed(4);
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4 mt-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wide">
          Live Trade Feed
        </h3>
        <span className="text-gray-500 text-xs">
          {recentTrades.length > 0 ? `${recentTrades.length} trades` : ''}
        </span>
      </div>

      <div
        ref={containerRef}
        className="font-mono text-sm h-48 overflow-y-auto"
      >
        {recentTrades.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span className="text-gray-500 animate-pulse">
              Waiting for trades...
            </span>
          </div>
        ) : (
          <div className="space-y-1">
            {recentTrades.map((trade, index) => {
              const isBuy = trade.side?.toLowerCase() === 'buy';
              const colorClass = isBuy ? 'text-green-400' : 'text-red-400';

              return (
                <div
                  key={trade.id || index}
                  className="flex items-center justify-between py-1 border-b border-gray-800 last:border-0"
                >
                  <div className="flex items-center space-x-3">
                    <span className={`${colorClass} font-bold w-10`}>
                      {trade.side?.toUpperCase() || '-'}
                    </span>
                    <span className="text-gray-300">
                      {formatQuantity(trade.quantity)}
                    </span>
                    <span className="text-gray-500">@</span>
                    <span className="text-gray-300">
                      ${formatPrice(trade.price)}
                    </span>
                  </div>
                  <span className="text-gray-500 text-xs">
                    {formatTimestamp(trade.timestamp || trade.created_at)}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
