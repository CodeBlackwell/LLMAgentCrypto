import { BasePage } from './base.page.js';

/**
 * New Backtest Form Page Object Model
 */
export class NewBacktestPage extends BasePage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    super(page);

    // Page title
    this.pageTitle = page.getByRole('heading', { name: 'New Backtest' });

    // Form element
    this.form = page.locator('form');

    // Form fields
    this.strategySelect = page.locator('#strategy_name');
    this.assetInput = page.locator('#asset');
    this.assetTypeSelect = page.locator('#asset_type');
    this.startDateInput = page.locator('#start_date');
    this.endDateInput = page.locator('#end_date');
    this.initialCashInput = page.locator('#initial_cash');
    this.thresholdInput = page.locator('#threshold');
    this.cashAtRiskInput = page.locator('#cash_at_risk');
    this.exchangeSelect = page.locator('#exchange');

    // Labels
    this.strategyLabel = page.locator('label:has-text("Strategy")');
    this.assetLabel = page.locator('label:has-text("Asset")');
    this.assetTypeLabel = page.locator('label:has-text("Asset Type")');
    this.startDateLabel = page.locator('label:has-text("Start Date")');
    this.endDateLabel = page.locator('label:has-text("End Date")');
    this.initialCashLabel = page.locator('label:has-text("Initial Cash")');
    this.thresholdLabel = page.locator('label:has-text("Threshold")');
    this.positionSizeLabel = page.locator('label:has-text("Position Size")');
    this.exchangeLabel = page.locator('label:has-text("Exchange")');

    // Buttons
    this.submitButton = page.getByRole('button', { name: 'Start Backtest' });
    this.cancelButton = page.getByRole('button', { name: 'Cancel' });
    this.loadingButton = page.getByRole('button', { name: 'Starting...' });

    // Error message
    this.errorMessage = page.locator('.bg-red-50');
  }

  /**
   * Navigate to New Backtest page
   * @param {string} [strategy] - Optional strategy to pre-select
   */
  async goto(strategy) {
    const url = strategy ? `/backtests/new?strategy=${strategy}` : '/backtests/new';
    await super.goto(url);
  }

  /**
   * Select a strategy
   * @param {string} strategyName
   */
  async selectStrategy(strategyName) {
    await this.strategySelect.selectOption(strategyName);
  }

  /**
   * Get available strategies from dropdown
   * @returns {Promise<string[]>}
   */
  async getAvailableStrategies() {
    const options = this.strategySelect.locator('option');
    const count = await options.count();
    const strategies = [];
    for (let i = 0; i < count; i++) {
      const value = await options.nth(i).getAttribute('value');
      if (value) {
        strategies.push(value);
      }
    }
    return strategies;
  }

  /**
   * Get the currently selected strategy
   * @returns {Promise<string>}
   */
  async getSelectedStrategy() {
    return await this.strategySelect.inputValue();
  }

  /**
   * Set the asset
   * @param {string} asset
   */
  async setAsset(asset) {
    await this.assetInput.clear();
    await this.assetInput.fill(asset);
  }

  /**
   * Select asset type
   * @param {string} assetType - 'crypto', 'stock', or 'forex'
   */
  async selectAssetType(assetType) {
    await this.assetTypeSelect.selectOption(assetType);
  }

  /**
   * Get the currently selected asset type
   * @returns {Promise<string>}
   */
  async getSelectedAssetType() {
    return await this.assetTypeSelect.inputValue();
  }

  /**
   * Set the date range
   * @param {string} startDate - Format: YYYY-MM-DD
   * @param {string} endDate - Format: YYYY-MM-DD
   */
  async setDateRange(startDate, endDate) {
    await this.startDateInput.fill(startDate);
    await this.endDateInput.fill(endDate);
  }

  /**
   * Set initial cash
   * @param {number} amount
   */
  async setInitialCash(amount) {
    await this.initialCashInput.clear();
    await this.initialCashInput.fill(amount.toString());
  }

  /**
   * Set threshold
   * @param {number} value - Value between 0 and 1
   */
  async setThreshold(value) {
    await this.thresholdInput.fill(value.toString());
  }

  /**
   * Set position size (cash at risk)
   * @param {number} value - Value between 0 and 1
   */
  async setPositionSize(value) {
    await this.cashAtRiskInput.fill(value.toString());
  }

  /**
   * Select exchange
   * @param {string} exchange - 'kraken', 'coinbase', 'binance', or 'bitfinex'
   */
  async selectExchange(exchange) {
    await this.exchangeSelect.selectOption(exchange);
  }

  /**
   * Check if exchange dropdown is visible
   * @returns {Promise<boolean>}
   */
  async isExchangeVisible() {
    return await this.exchangeLabel.isVisible();
  }

  /**
   * Fill the entire form
   * @param {Object} data - Form data
   */
  async fillForm(data) {
    if (data.strategy_name) {
      await this.selectStrategy(data.strategy_name);
    }
    if (data.asset) {
      await this.setAsset(data.asset);
    }
    if (data.asset_type) {
      await this.selectAssetType(data.asset_type);
    }
    if (data.start_date) {
      await this.startDateInput.fill(data.start_date);
    }
    if (data.end_date) {
      await this.endDateInput.fill(data.end_date);
    }
    if (data.initial_cash) {
      await this.setInitialCash(data.initial_cash);
    }
    if (data.threshold !== undefined) {
      await this.setThreshold(data.threshold);
    }
    if (data.cash_at_risk !== undefined) {
      await this.setPositionSize(data.cash_at_risk);
    }
    if (data.exchange && (await this.isExchangeVisible())) {
      await this.selectExchange(data.exchange);
    }
  }

  /**
   * Submit the form
   */
  async submit() {
    await this.submitButton.click();
  }

  /**
   * Cancel and go back
   */
  async cancel() {
    await this.cancelButton.click();
  }

  /**
   * Check if submit button is in loading state
   * @returns {Promise<boolean>}
   */
  async isSubmitting() {
    return await this.loadingButton.isVisible();
  }

  /**
   * Check if submit button is disabled
   * @returns {Promise<boolean>}
   */
  async isSubmitDisabled() {
    return await this.submitButton.isDisabled();
  }

  /**
   * Get error message text
   * @returns {Promise<string|null>}
   */
  async getErrorMessage() {
    if (await this.errorMessage.isVisible()) {
      return await this.errorMessage.textContent();
    }
    return null;
  }

  /**
   * Check if error is displayed
   * @returns {Promise<boolean>}
   */
  async hasError() {
    return await this.errorMessage.isVisible();
  }

  /**
   * Get all default values from the form
   * @returns {Promise<Object>}
   */
  async getFormDefaults() {
    return {
      asset: await this.assetInput.inputValue(),
      asset_type: await this.assetTypeSelect.inputValue(),
      start_date: await this.startDateInput.inputValue(),
      end_date: await this.endDateInput.inputValue(),
      initial_cash: await this.initialCashInput.inputValue(),
      threshold: await this.thresholdInput.inputValue(),
      cash_at_risk: await this.cashAtRiskInput.inputValue(),
      exchange: (await this.isExchangeVisible()) ? await this.exchangeSelect.inputValue() : null
    };
  }

  /**
   * Check if all required form fields are visible
   * @returns {Promise<boolean>}
   */
  async hasAllFields() {
    return (
      (await this.strategyLabel.isVisible()) &&
      (await this.assetLabel.isVisible()) &&
      (await this.assetTypeLabel.isVisible()) &&
      (await this.startDateLabel.isVisible()) &&
      (await this.endDateLabel.isVisible()) &&
      (await this.initialCashLabel.isVisible()) &&
      (await this.thresholdLabel.isVisible()) &&
      (await this.positionSizeLabel.isVisible())
    );
  }
}
