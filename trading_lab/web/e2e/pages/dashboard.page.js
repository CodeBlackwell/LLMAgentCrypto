import { BasePage } from './base.page.js';

/**
 * Dashboard Page Object Model
 */
export class DashboardPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // Page title
    this.pageTitle = page.getByRole('heading', { name: 'Dashboard' });

    // Stat cards
    this.totalStrategiesCard = page.locator('text=Total Strategies').locator('..');
    this.completedBacktestsCard = page.locator('text=Completed Backtests').locator('..');
    this.runningCard = page.locator('text=Running').locator('..');
    this.avgReturnCard = page.locator('text=Avg Return').locator('..');

    // Recent backtests section
    this.recentBacktestsSection = page.locator('text=Recent Backtests').locator('..');
    this.recentBacktestsTable = page.locator('table').first();
    this.viewAllLink = page.getByRole('link', { name: 'View all' });

    // Empty state
    this.emptyState = page.locator('text=No backtests yet');
    this.runFirstBacktestLink = page.getByRole('link', { name: 'Run Your First Backtest' });

    // Quick action cards
    this.quickActionNewBacktest = page.locator('h4:has-text("New Backtest")').locator('..');
    this.quickActionStrategies = page.locator('h4:has-text("View Strategies")').locator('..');
    this.quickActionCompare = page.locator('h4:has-text("Compare Results")').locator('..');
  }

  /**
   * Navigate to Dashboard
   */
  async goto() {
    await super.goto('/');
  }

  /**
   * Get the value from a stat card
   * @param {string} label - Card label (e.g., 'Total Strategies')
   * @returns {Promise<string>}
   */
  async getStatValue(label) {
    const card = this.page.locator(`text=${label}`).locator('..');
    const value = card.locator('.text-2xl, .text-3xl').first();
    return await value.textContent();
  }

  /**
   * Get the count of recent backtests in the table
   * @returns {Promise<number>}
   */
  async getRecentBacktestsCount() {
    const rows = this.recentBacktestsTable.locator('tbody tr');
    return await rows.count();
  }

  /**
   * Click on a recent backtest by strategy name
   * @param {string} strategyName
   */
  async clickRecentBacktest(strategyName) {
    const link = this.recentBacktestsTable.getByRole('link', { name: strategyName }).first();
    await link.click();
  }

  /**
   * Get status badges from recent backtests
   * @returns {Promise<string[]>}
   */
  async getBacktestStatuses() {
    const badges = this.recentBacktestsTable.locator('[class*="bg-"][class*="-100"]');
    const count = await badges.count();
    const statuses = [];
    for (let i = 0; i < count; i++) {
      const text = await badges.nth(i).textContent();
      statuses.push(text.trim());
    }
    return statuses;
  }

  /**
   * Click the New Backtest quick action card
   */
  async clickNewBacktestQuickAction() {
    await this.quickActionNewBacktest.click();
  }

  /**
   * Click the View Strategies quick action card
   */
  async clickStrategiesQuickAction() {
    await this.quickActionStrategies.click();
  }

  /**
   * Check if the dashboard is showing empty state
   * @returns {Promise<boolean>}
   */
  async isEmptyState() {
    return await this.emptyState.isVisible();
  }

  /**
   * Check if stats are loaded
   * @returns {Promise<boolean>}
   */
  async areStatsLoaded() {
    const totalStrategies = await this.getStatValue('Total Strategies');
    return totalStrategies !== null && totalStrategies !== '';
  }
}
