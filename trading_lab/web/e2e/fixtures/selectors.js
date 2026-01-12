/**
 * Shared selectors for Playwright tests
 * Use these constants to keep selectors consistent across tests
 */

// Navigation
export const NAV = {
  header: 'header',
  logo: 'header >> text=Trading Lab',
  dashboardLink: 'nav >> a:has-text("Dashboard")',
  strategiesLink: 'nav >> a:has-text("Strategies")',
  backtestsLink: 'nav >> a:has-text("Backtests")',
  newBacktestBtn: 'header >> a:has-text("New Backtest")'
};

// Status badges
export const STATUS_BADGE = {
  completed: '.bg-green-100',
  running: '.bg-blue-100',
  pending: '.bg-yellow-100',
  failed: '.bg-red-100',
  cancelled: '.bg-gray-100'
};

// Dashboard
export const DASHBOARD = {
  pageTitle: 'h1:has-text("Dashboard")',
  statsSection: '[data-testid="stats-section"]',
  totalStrategiesCard: 'text=Total Strategies',
  completedBacktestsCard: 'text=Completed Backtests',
  runningCard: 'text=Running',
  avgReturnCard: 'text=Avg Return',
  recentBacktestsTable: 'table',
  emptyState: 'text=No backtests yet',
  quickActionNewBacktest: 'h4:has-text("New Backtest")',
  quickActionStrategies: 'h4:has-text("View Strategies")',
  quickActionCompare: 'h4:has-text("Compare Results")'
};

// Strategies page
export const STRATEGIES = {
  pageTitle: 'h1:has-text("Strategies")',
  strategyCard: '.card:has-text("Run Backtest")',
  strategyName: 'h3',
  strategyDescription: 'p.text-gray-600',
  assetTypeBadge: '.bg-gray-100',
  providerInfo: 'text=Provider:',
  runBacktestLink: 'a:has-text("Run Backtest")',
  emptyState: 'text=No strategies registered',
  loadingState: 'text=Loading strategies'
};

// Backtests page
export const BACKTESTS = {
  pageTitle: 'h1:has-text("Backtests")',
  newBacktestBtn: 'a:has-text("New Backtest")',
  table: 'table',
  tableHeader: 'thead',
  tableBody: 'tbody',
  strategyColumn: 'th:has-text("Strategy")',
  assetColumn: 'th:has-text("Asset")',
  dateRangeColumn: 'th:has-text("Date Range")',
  returnColumn: 'th:has-text("Return")',
  sharpeColumn: 'th:has-text("Sharpe")',
  statusColumn: 'th:has-text("Status")',
  createdColumn: 'th:has-text("Created")',
  emptyState: 'text=No backtests yet',
  runFirstBacktestLink: 'a:has-text("Run Your First Backtest")',
  positiveReturn: '.text-green-600',
  negativeReturn: '.text-red-600',
  nullValue: '.text-gray-400'
};

// New Backtest form
export const NEW_BACKTEST = {
  pageTitle: 'h1:has-text("New Backtest")',
  form: 'form',
  strategySelect: '#strategy_name',
  assetInput: '#asset',
  assetTypeSelect: '#asset_type',
  startDateInput: '#start_date',
  endDateInput: '#end_date',
  initialCashInput: '#initial_cash',
  thresholdInput: '#threshold',
  thresholdSlider: 'input[type="range"][id="threshold"]',
  cashAtRiskInput: '#cash_at_risk',
  cashAtRiskSlider: 'input[type="range"][id="cash_at_risk"]',
  exchangeSelect: '#exchange',
  submitBtn: 'button:has-text("Start Backtest")',
  cancelBtn: 'button:has-text("Cancel")',
  loadingBtn: 'button:has-text("Starting...")',
  errorMessage: '.bg-red-50',
  strategyLabel: 'label:has-text("Strategy")',
  assetLabel: 'label:has-text("Asset")',
  assetTypeLabel: 'label:has-text("Asset Type")',
  startDateLabel: 'label:has-text("Start Date")',
  endDateLabel: 'label:has-text("End Date")',
  initialCashLabel: 'label:has-text("Initial Cash")',
  thresholdLabel: 'label:has-text("Threshold")',
  positionSizeLabel: 'label:has-text("Position Size")',
  exchangeLabel: 'label:has-text("Exchange")'
};

// Backtest Detail page
export const BACKTEST_DETAIL = {
  pageTitle: 'h1',
  statusBadge: '[class*="bg-"][class*="-100"]',
  assetInfo: 'text=/.*on.*/',
  cancelBtn: 'button:has-text("Cancel")',
  deleteBtn: 'button:has-text("Delete")',
  backLink: 'a:has-text("Back")',
  metricsSection: 'text=Performance Metrics',
  initialCashCard: 'text=Initial Cash',
  finalValueCard: 'text=Final Value',
  totalReturnCard: 'text=Total Return',
  winRateCard: 'text=Win Rate',
  sharpeRatioCard: 'text=Sharpe Ratio',
  maxDrawdownCard: 'text=Max Drawdown',
  totalTradesCard: 'text=Total Trades',
  dateRangeCard: 'text=Date Range',
  equityCurveSection: 'text=Equity Curve',
  chart: '.recharts-wrapper',
  tradesSection: 'text=Trades',
  tradesTable: 'table',
  timeColumn: 'th:has-text("Time")',
  sideColumn: 'th:has-text("Side")',
  quantityColumn: 'th:has-text("Quantity")',
  priceColumn: 'th:has-text("Price")',
  totalColumn: 'th:has-text("Total")',
  confidenceColumn: 'th:has-text("Confidence")',
  buyTrade: '.text-green-600:has-text("BUY")',
  sellTrade: '.text-red-600:has-text("SELL")',
  errorState: 'text=Failed to load backtest',
  loadingState: 'text=Loading'
};

// Common elements
export const COMMON = {
  loadingSpinner: '[class*="animate-spin"]',
  card: '.card',
  table: 'table',
  button: 'button',
  link: 'a',
  input: 'input',
  select: 'select',
  errorAlert: '.bg-red-50',
  successAlert: '.bg-green-50'
};
