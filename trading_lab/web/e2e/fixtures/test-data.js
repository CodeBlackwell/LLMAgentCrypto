/**
 * Mock data for Playwright E2E tests
 */

export const TEST_STRATEGIES = {
  strategies: [
    {
      name: 'random',
      description: 'Random signal generation for testing purposes',
      default_provider: 'random',
      asset_types: ['crypto', 'stock'],
      class_name: 'RandomStrategy'
    },
    {
      name: 'sentiment',
      description: 'News sentiment analysis trading strategy',
      default_provider: 'ollama',
      asset_types: ['crypto', 'stock', 'forex'],
      class_name: 'SentimentStrategy'
    },
    {
      name: 'technical',
      description: 'Technical indicator based strategy',
      default_provider: 'technical',
      asset_types: ['crypto', 'stock'],
      class_name: 'TechnicalStrategy'
    }
  ]
};

export const TEST_BACKTESTS = {
  backtests: [
    {
      id: 1,
      strategy_name: 'random',
      asset: 'BTC/USD',
      asset_type: 'crypto',
      exchange: 'kraken',
      status: 'completed',
      start_date: '2024-01-01',
      end_date: '2024-06-30',
      initial_cash: 100000,
      final_value: 115250,
      total_return: 15.25,
      total_trades: 42,
      win_rate: 0.65,
      sharpe_ratio: 1.45,
      max_drawdown: 0.12,
      created_at: '2024-07-01T10:00:00Z',
      completed_at: '2024-07-01T10:05:00Z'
    },
    {
      id: 2,
      strategy_name: 'sentiment',
      asset: 'ETH/USD',
      asset_type: 'crypto',
      exchange: 'coinbase',
      status: 'running',
      start_date: '2024-02-01',
      end_date: '2024-07-01',
      initial_cash: 50000,
      final_value: null,
      total_return: null,
      total_trades: null,
      win_rate: null,
      sharpe_ratio: null,
      max_drawdown: null,
      created_at: '2024-07-01T12:00:00Z',
      completed_at: null
    },
    {
      id: 3,
      strategy_name: 'technical',
      asset: 'AAPL',
      asset_type: 'stock',
      exchange: null,
      status: 'pending',
      start_date: '2024-03-01',
      end_date: '2024-06-01',
      initial_cash: 75000,
      final_value: null,
      total_return: null,
      total_trades: null,
      win_rate: null,
      sharpe_ratio: null,
      max_drawdown: null,
      created_at: '2024-07-01T14:00:00Z',
      completed_at: null
    },
    {
      id: 4,
      strategy_name: 'random',
      asset: 'EUR/USD',
      asset_type: 'forex',
      exchange: null,
      status: 'failed',
      start_date: '2024-01-15',
      end_date: '2024-04-15',
      initial_cash: 25000,
      final_value: null,
      total_return: null,
      total_trades: null,
      win_rate: null,
      sharpe_ratio: null,
      max_drawdown: null,
      created_at: '2024-07-01T08:00:00Z',
      completed_at: null,
      error: 'Provider connection failed'
    },
    {
      id: 5,
      strategy_name: 'sentiment',
      asset: 'SOL/USD',
      asset_type: 'crypto',
      exchange: 'binance',
      status: 'completed',
      start_date: '2024-01-01',
      end_date: '2024-03-31',
      initial_cash: 30000,
      final_value: 24600,
      total_return: -18.0,
      total_trades: 28,
      win_rate: 0.35,
      sharpe_ratio: -0.82,
      max_drawdown: 0.25,
      created_at: '2024-04-01T09:00:00Z',
      completed_at: '2024-04-01T09:10:00Z'
    }
  ],
  total: 5
};

export const COMPLETED_BACKTEST = {
  id: 1,
  strategy_name: 'random',
  asset: 'BTC/USD',
  asset_type: 'crypto',
  exchange: 'kraken',
  status: 'completed',
  start_date: '2024-01-01',
  end_date: '2024-06-30',
  initial_cash: 100000,
  final_value: 115250,
  total_return: 15.25,
  total_trades: 42,
  win_rate: 0.65,
  sharpe_ratio: 1.45,
  max_drawdown: 0.12,
  created_at: '2024-07-01T10:00:00Z',
  completed_at: '2024-07-01T10:05:00Z'
};

export const RUNNING_BACKTEST = {
  id: 2,
  strategy_name: 'sentiment',
  asset: 'ETH/USD',
  asset_type: 'crypto',
  exchange: 'coinbase',
  status: 'running',
  start_date: '2024-02-01',
  end_date: '2024-07-01',
  initial_cash: 50000,
  final_value: null,
  total_return: null,
  total_trades: null,
  win_rate: null,
  sharpe_ratio: null,
  max_drawdown: null,
  created_at: '2024-07-01T12:00:00Z',
  completed_at: null
};

export const BACKTEST_RESULTS = {
  backtest: COMPLETED_BACKTEST,
  trades: [
    {
      id: 1,
      timestamp: '2024-01-15T10:30:00Z',
      asset: 'BTC/USD',
      side: 'buy',
      quantity: 0.5,
      price: 42000,
      total_value: 21000,
      signal_confidence: 0.85,
      status: 'filled'
    },
    {
      id: 2,
      timestamp: '2024-02-01T14:15:00Z',
      asset: 'BTC/USD',
      side: 'sell',
      quantity: 0.25,
      price: 44500,
      total_value: 11125,
      signal_confidence: 0.72,
      status: 'filled'
    },
    {
      id: 3,
      timestamp: '2024-02-20T09:45:00Z',
      asset: 'BTC/USD',
      side: 'buy',
      quantity: 0.3,
      price: 51000,
      total_value: 15300,
      signal_confidence: 0.91,
      status: 'filled'
    },
    {
      id: 4,
      timestamp: '2024-03-15T16:00:00Z',
      asset: 'BTC/USD',
      side: 'sell',
      quantity: 0.55,
      price: 68000,
      total_value: 37400,
      signal_confidence: 0.88,
      status: 'filled'
    },
    {
      id: 5,
      timestamp: '2024-04-10T11:30:00Z',
      asset: 'BTC/USD',
      side: 'buy',
      quantity: 0.4,
      price: 62000,
      total_value: 24800,
      signal_confidence: 0.76,
      status: 'filled'
    }
  ],
  daily_stats: [
    { date: '2024-01-01', portfolio_value: 100000, cash: 100000, daily_return: 0, cumulative_return: 0 },
    { date: '2024-01-15', portfolio_value: 101200, cash: 79000, daily_return: 0.012, cumulative_return: 0.012 },
    { date: '2024-02-01', portfolio_value: 103500, cash: 90125, daily_return: 0.023, cumulative_return: 0.035 },
    { date: '2024-02-20', portfolio_value: 105800, cash: 74825, daily_return: 0.022, cumulative_return: 0.058 },
    { date: '2024-03-15', portfolio_value: 112400, cash: 112225, daily_return: 0.062, cumulative_return: 0.124 },
    { date: '2024-04-10', portfolio_value: 108200, cash: 87425, daily_return: -0.037, cumulative_return: 0.082 },
    { date: '2024-05-01', portfolio_value: 111500, cash: 87425, daily_return: 0.031, cumulative_return: 0.115 },
    { date: '2024-06-01', portfolio_value: 114000, cash: 87425, daily_return: 0.022, cumulative_return: 0.140 },
    { date: '2024-06-30', portfolio_value: 115250, cash: 115250, daily_return: 0.011, cumulative_return: 0.1525 }
  ]
};

export const VALID_BACKTEST_FORM = {
  strategy_name: 'random',
  asset: 'BTC/USD',
  asset_type: 'crypto',
  start_date: '2024-01-01',
  end_date: '2024-06-30',
  initial_cash: 100000,
  threshold: 0.7,
  cash_at_risk: 0.25,
  exchange: 'kraken'
};

export const CREATE_BACKTEST_RESPONSE = {
  backtest_id: 100,
  status: 'pending',
  message: 'Backtest submitted successfully'
};

export const EMPTY_BACKTESTS = {
  backtests: [],
  total: 0
};

export const EMPTY_STRATEGIES = {
  strategies: []
};
