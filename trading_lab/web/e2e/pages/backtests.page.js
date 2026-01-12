import { BasePage } from './base.page.js';

/**
 * Backtests List Page Object Model
 */
export class BacktestsPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // Page elements
    this.pageTitle = page.getByRole('heading', { name: 'Backtests' });
    this.newBacktestButton = page.locator('a:has-text("New Backtest")').first();

    // Table elements
    this.table = page.locator('table');
    this.tableHeader = page.locator('thead');
    this.tableBody = page.locator('tbody');

    // Table columns
    this.strategyColumn = page.locator('th:has-text("Strategy")');
    this.assetColumn = page.locator('th:has-text("Asset")');
    this.dateRangeColumn = page.locator('th:has-text("Date Range")');
    this.returnColumn = page.locator('th:has-text("Return")');
    this.sharpeColumn = page.locator('th:has-text("Sharpe")');
    this.statusColumn = page.locator('th:has-text("Status")');
    this.createdColumn = page.locator('th:has-text("Created")');

    // Empty state
    this.emptyState = page.locator('text=No backtests yet');
    this.runFirstBacktestLink = page.getByRole('link', { name: 'Run Your First Backtest' });

    // Loading state
    this.loadingState = page.locator('text=Loading');
  }

  /**
   * Navigate to Backtests page
   */
  async goto() {
    await super.goto('/backtests');
  }

  /**
   * Get all table rows
   * @returns {import('@playwright/test').Locator}
   */
  getRows() {
    return this.tableBody.locator('tr');
  }

  /**
   * Get the count of backtests in the table
   * @returns {Promise<number>}
   */
  async getBacktestCount() {
    return await this.getRows().count();
  }

  /**
   * Get a row by index
   * @param {number} index - Row index (0-based)
   * @returns {import('@playwright/test').Locator}
   */
  getRow(index) {
    return this.getRows().nth(index);
  }

  /**
   * Get a row by strategy name
   * @param {string} strategyName
   * @returns {import('@playwright/test').Locator}
   */
  getRowByStrategy(strategyName) {
    return this.tableBody.locator('tr').filter({ hasText: strategyName });
  }

  /**
   * Click on a backtest to view details
   * @param {string} strategyName
   */
  async clickBacktest(strategyName) {
    const row = this.getRowByStrategy(strategyName);
    const link = row.getByRole('link').first();
    await link.click();
  }

  /**
   * Get the status of a backtest
   * @param {number} index - Row index
   * @returns {Promise<string>}
   */
  async getStatus(index) {
    const row = this.getRow(index);
    const badge = row.locator('[class*="bg-"][class*="-100"]');
    return await badge.textContent();
  }

  /**
   * Get the return value of a backtest
   * @param {number} index - Row index
   * @returns {Promise<string>}
   */
  async getReturn(index) {
    const row = this.getRow(index);
    // Return is usually in a colored span
    const returnCell = row.locator('.text-green-600, .text-red-600, .text-gray-400').first();
    return await returnCell.textContent();
  }

  /**
   * Check if a return value is positive (green)
   * @param {number} index - Row index
   * @returns {Promise<boolean>}
   */
  async isReturnPositive(index) {
    const row = this.getRow(index);
    const greenReturn = row.locator('.text-green-600');
    return await greenReturn.isVisible();
  }

  /**
   * Check if a return value is negative (red)
   * @param {number} index - Row index
   * @returns {Promise<boolean>}
   */
  async isReturnNegative(index) {
    const row = this.getRow(index);
    const redReturn = row.locator('.text-red-600');
    return await redReturn.isVisible();
  }

  /**
   * Get all visible status badges
   * @returns {Promise<string[]>}
   */
  async getAllStatuses() {
    const badges = this.tableBody.locator('[class*="bg-"][class*="-100"]');
    const count = await badges.count();
    const statuses = [];
    for (let i = 0; i < count; i++) {
      statuses.push((await badges.nth(i).textContent()).trim());
    }
    return statuses;
  }

  /**
   * Click the New Backtest button
   */
  async clickNewBacktest() {
    await this.newBacktestButton.click();
  }

  /**
   * Check if empty state is visible
   * @returns {Promise<boolean>}
   */
  async isEmpty() {
    return await this.emptyState.isVisible();
  }

  /**
   * Check if table has all expected columns
   * @returns {Promise<boolean>}
   */
  async hasAllColumns() {
    return (
      (await this.strategyColumn.isVisible()) &&
      (await this.assetColumn.isVisible()) &&
      (await this.returnColumn.isVisible()) &&
      (await this.statusColumn.isVisible())
    );
  }

  /**
   * Get the subtitle text (shows count)
   * @returns {Promise<string>}
   */
  async getSubtitle() {
    const subtitle = this.page.locator('p.text-gray-600').first();
    return await subtitle.textContent();
  }
}
