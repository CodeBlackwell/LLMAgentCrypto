import { BasePage } from './base.page.js';

/**
 * Strategies Page Object Model
 */
export class StrategiesPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // Page elements
    this.pageTitle = page.getByRole('heading', { name: 'Strategies' });
    this.subtitle = page.locator('text=Available trading strategies');

    // Loading and empty states
    this.loadingState = page.locator('text=Loading strategies');
    this.emptyState = page.locator('text=No strategies registered');
    this.errorState = page.locator('text=Failed to load strategies');

    // Strategy cards container
    this.strategiesGrid = page.locator('.grid');
  }

  /**
   * Navigate to Strategies page
   */
  async goto() {
    await super.goto('/strategies');
  }

  /**
   * Get all strategy cards
   * @returns {import('@playwright/test').Locator}
   */
  getStrategyCards() {
    return this.page.locator('.card').filter({ hasText: 'Run Backtest' });
  }

  /**
   * Get the count of strategy cards
   * @returns {Promise<number>}
   */
  async getStrategyCount() {
    return await this.getStrategyCards().count();
  }

  /**
   * Get a strategy card by name
   * @param {string} name - Strategy name
   * @returns {import('@playwright/test').Locator}
   */
  getStrategyCard(name) {
    return this.page.locator('.card').filter({ hasText: name }).filter({ hasText: 'Run Backtest' });
  }

  /**
   * Get strategy name from a card
   * @param {number} index - Card index (0-based)
   * @returns {Promise<string>}
   */
  async getStrategyName(index) {
    const card = this.getStrategyCards().nth(index);
    const name = card.locator('h3');
    return await name.textContent();
  }

  /**
   * Get strategy description from a card
   * @param {string} name - Strategy name
   * @returns {Promise<string>}
   */
  async getStrategyDescription(name) {
    const card = this.getStrategyCard(name);
    const description = card.locator('p.text-gray-600').first();
    return await description.textContent();
  }

  /**
   * Get asset types for a strategy
   * @param {string} name - Strategy name
   * @returns {Promise<string[]>}
   */
  async getAssetTypes(name) {
    const card = this.getStrategyCard(name);
    const badges = card.locator('.bg-gray-100');
    const count = await badges.count();
    const types = [];
    for (let i = 0; i < count; i++) {
      const text = await badges.nth(i).textContent();
      types.push(text.trim());
    }
    return types;
  }

  /**
   * Get provider info for a strategy
   * @param {string} name - Strategy name
   * @returns {Promise<string>}
   */
  async getProviderInfo(name) {
    const card = this.getStrategyCard(name);
    const provider = card.locator('text=Provider:').locator('..');
    return await provider.textContent();
  }

  /**
   * Click Run Backtest for a strategy
   * @param {string} name - Strategy name
   */
  async clickRunBacktest(name) {
    const card = this.getStrategyCard(name);
    const link = card.getByRole('link', { name: 'Run Backtest' });
    await link.click();
  }

  /**
   * Get the Run Backtest link href for a strategy
   * @param {string} name - Strategy name
   * @returns {Promise<string>}
   */
  async getRunBacktestHref(name) {
    const card = this.getStrategyCard(name);
    const link = card.getByRole('link', { name: 'Run Backtest' });
    return await link.getAttribute('href');
  }

  /**
   * Check if loading state is visible
   * @returns {Promise<boolean>}
   */
  async isLoading() {
    return await this.loadingState.isVisible();
  }

  /**
   * Check if empty state is visible
   * @returns {Promise<boolean>}
   */
  async isEmpty() {
    return await this.emptyState.isVisible();
  }

  /**
   * Check if error state is visible
   * @returns {Promise<boolean>}
   */
  async hasError() {
    return await this.errorState.isVisible();
  }
}
