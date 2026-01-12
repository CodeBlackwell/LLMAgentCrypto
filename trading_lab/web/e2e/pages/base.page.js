/**
 * Base Page Object Model
 * Contains shared navigation and utility methods
 */
export class BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;

    // Header elements
    this.header = page.locator('header');
    this.logo = page.locator('header').getByText('Trading Lab');

    // Navigation links
    this.navDashboard = page.getByRole('link', { name: 'Dashboard' });
    this.navStrategies = page.getByRole('link', { name: 'Strategies' });
    this.navBacktests = page.getByRole('link', { name: 'Backtests' });
    this.newBacktestBtn = page.locator('header').getByRole('link', { name: 'New Backtest' });
  }

  /**
   * Navigate to a path
   * @param {string} path - URL path
   */
  async goto(path = '/') {
    await this.page.goto(path);
  }

  /**
   * Wait for network to be idle
   */
  async waitForApi() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Wait for a specific API response
   * @param {string} urlPattern - URL pattern to match
   */
  async waitForApiResponse(urlPattern) {
    await this.page.waitForResponse((response) =>
      response.url().includes(urlPattern) && response.status() === 200
    );
  }

  /**
   * Navigate to Dashboard
   */
  async goToDashboard() {
    await this.navDashboard.click();
    await this.page.waitForURL('/');
  }

  /**
   * Navigate to Strategies
   */
  async goToStrategies() {
    await this.navStrategies.click();
    await this.page.waitForURL('/strategies');
  }

  /**
   * Navigate to Backtests
   */
  async goToBacktests() {
    await this.navBacktests.click();
    await this.page.waitForURL('/backtests');
  }

  /**
   * Navigate to New Backtest form
   */
  async goToNewBacktest() {
    await this.newBacktestBtn.click();
    await this.page.waitForURL(/\/backtests\/new/);
  }

  /**
   * Get the current URL path
   * @returns {string}
   */
  getCurrentPath() {
    return new URL(this.page.url()).pathname;
  }

  /**
   * Check if an element is visible
   * @param {import('@playwright/test').Locator} locator
   * @returns {Promise<boolean>}
   */
  async isVisible(locator) {
    return await locator.isVisible();
  }

  /**
   * Wait for loading to complete
   */
  async waitForLoadingToComplete() {
    // Wait for any loading spinners to disappear
    const spinner = this.page.locator('[class*="animate-spin"]');
    if (await spinner.isVisible({ timeout: 1000 }).catch(() => false)) {
      await spinner.waitFor({ state: 'hidden', timeout: 30000 });
    }
  }
}
