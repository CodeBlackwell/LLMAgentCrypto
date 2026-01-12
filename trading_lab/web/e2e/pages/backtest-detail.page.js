import { BasePage } from './base.page.js';

/**
 * Backtest Detail Page Object Model
 */
export class BacktestDetailPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // Header elements
    this.pageTitle = page.locator('h1').first();
    this.statusBadge = page.locator('[class*="bg-"][class*="-100"]').first();
    this.assetInfo = page.locator('text=/.*on.*/').first();

    // Action buttons
    this.cancelButton = page.getByRole('button', { name: 'Cancel' });
    this.deleteButton = page.getByRole('button', { name: 'Delete' });
    this.backLink = page.getByRole('link', { name: /Back/i });

    // Metric cards
    this.metricsSection = page.locator('text=Performance Metrics').locator('..');
    this.initialCashCard = page.locator('text=Initial Cash').locator('..');
    this.finalValueCard = page.locator('text=Final Value').locator('..');
    this.totalReturnCard = page.locator('text=Total Return').locator('..');
    this.winRateCard = page.locator('text=Win Rate').locator('..');
    this.sharpeRatioCard = page.locator('text=Sharpe Ratio').locator('..');
    this.maxDrawdownCard = page.locator('text=Max Drawdown').locator('..');
    this.totalTradesCard = page.locator('text=Total Trades').locator('..');
    this.dateRangeCard = page.locator('text=Date Range').locator('..');

    // Equity curve chart
    this.equityCurveSection = page.locator('text=Equity Curve').locator('..');
    this.chart = page.locator('.recharts-wrapper');

    // Trades table
    this.tradesSection = page.locator('text=Trades').locator('..').first();
    this.tradesTable = page.locator('table').last();

    // Error and loading states
    this.errorState = page.locator('text=Failed to load backtest');
    this.loadingState = page.locator('text=Loading');
  }

  /**
   * Navigate to a backtest detail page
   * @param {number} id - Backtest ID
   */
  async goto(id) {
    await super.goto(`/backtests/${id}`);
  }

  /**
   * Get the strategy name from the title
   * @returns {Promise<string>}
   */
  async getStrategyName() {
    return await this.pageTitle.textContent();
  }

  /**
   * Get the current status
   * @returns {Promise<string>}
   */
  async getStatus() {
    const text = await this.statusBadge.textContent();
    return text.trim();
  }

  /**
   * Check if the backtest is completed
   * @returns {Promise<boolean>}
   */
  async isCompleted() {
    const status = await this.getStatus();
    return status.toLowerCase() === 'completed';
  }

  /**
   * Check if the backtest is running
   * @returns {Promise<boolean>}
   */
  async isRunning() {
    const status = await this.getStatus();
    return status.toLowerCase() === 'running';
  }

  /**
   * Check if cancel button is visible (only for running backtests)
   * @returns {Promise<boolean>}
   */
  async isCancelVisible() {
    return await this.cancelButton.isVisible();
  }

  /**
   * Click the cancel button
   */
  async clickCancel() {
    await this.cancelButton.click();
  }

  /**
   * Click the delete button
   */
  async clickDelete() {
    await this.deleteButton.click();
  }

  /**
   * Go back to backtests list
   */
  async goBack() {
    await this.backLink.click();
  }

  /**
   * Get a metric value by label
   * @param {string} label - Metric label (e.g., 'Total Return', 'Win Rate')
   * @returns {Promise<string>}
   */
  async getMetricValue(label) {
    const card = this.page.locator(`text=${label}`).locator('..');
    const value = card.locator('.text-2xl, .text-3xl, .text-xl').first();
    return await value.textContent();
  }

  /**
   * Get the total return value
   * @returns {Promise<string>}
   */
  async getTotalReturn() {
    return await this.getMetricValue('Total Return');
  }

  /**
   * Check if total return is positive (green)
   * @returns {Promise<boolean>}
   */
  async isReturnPositive() {
    const card = this.totalReturnCard;
    const greenValue = card.locator('.text-green-600');
    return await greenValue.isVisible();
  }

  /**
   * Check if total return is negative (red)
   * @returns {Promise<boolean>}
   */
  async isReturnNegative() {
    const card = this.totalReturnCard;
    const redValue = card.locator('.text-red-600');
    return await redValue.isVisible();
  }

  /**
   * Check if the equity curve chart is visible
   * @returns {Promise<boolean>}
   */
  async isChartVisible() {
    return await this.chart.isVisible();
  }

  /**
   * Get the trade count from the trades section
   * @returns {Promise<number>}
   */
  async getTradeCount() {
    const rows = this.tradesTable.locator('tbody tr');
    return await rows.count();
  }

  /**
   * Get trade information by index
   * @param {number} index - Trade index (0-based)
   * @returns {Promise<Object>}
   */
  async getTradeInfo(index) {
    const row = this.tradesTable.locator('tbody tr').nth(index);
    const cells = row.locator('td');

    return {
      time: await cells.nth(0).textContent(),
      side: await cells.nth(1).textContent(),
      quantity: await cells.nth(2).textContent(),
      price: await cells.nth(3).textContent(),
      total: await cells.nth(4).textContent(),
      confidence: await cells.nth(5).textContent()
    };
  }

  /**
   * Check if there are buy trades (green)
   * @returns {Promise<boolean>}
   */
  async hasBuyTrades() {
    const buyBadge = this.tradesTable.locator('.text-green-600:has-text("BUY")');
    return (await buyBadge.count()) > 0;
  }

  /**
   * Check if there are sell trades (red)
   * @returns {Promise<boolean>}
   */
  async hasSellTrades() {
    const sellBadge = this.tradesTable.locator('.text-red-600:has-text("SELL")');
    return (await sellBadge.count()) > 0;
  }

  /**
   * Check if all metric cards are visible
   * @returns {Promise<boolean>}
   */
  async hasAllMetrics() {
    const metrics = [
      'Initial Cash',
      'Final Value',
      'Total Return',
      'Win Rate',
      'Sharpe Ratio',
      'Max Drawdown',
      'Total Trades',
      'Date Range'
    ];

    for (const metric of metrics) {
      const isVisible = await this.page.locator(`text=${metric}`).isVisible();
      if (!isVisible) return false;
    }
    return true;
  }

  /**
   * Check if error state is visible
   * @returns {Promise<boolean>}
   */
  async hasError() {
    return await this.errorState.isVisible();
  }

  /**
   * Check if loading state is visible
   * @returns {Promise<boolean>}
   */
  async isLoading() {
    return await this.loadingState.isVisible();
  }

  /**
   * Wait for the page to finish loading
   */
  async waitForLoad() {
    await this.page.waitForLoadState('networkidle');
    // Wait for either content or error
    await this.page.waitForSelector('h1, text=Failed');
  }

  /**
   * Accept the delete confirmation dialog
   */
  async confirmDelete() {
    this.page.once('dialog', (dialog) => dialog.accept());
    await this.clickDelete();
  }

  /**
   * Dismiss the delete confirmation dialog
   */
  async cancelDelete() {
    this.page.once('dialog', (dialog) => dialog.dismiss());
    await this.clickDelete();
  }
}
