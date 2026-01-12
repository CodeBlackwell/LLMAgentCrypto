import { test, expect } from '@playwright/test';
import { StrategiesPage } from '../../pages/strategies.page.js';
import { mockStrategiesApi, mockApiError, mockApiWithDelay } from '../../fixtures/api-mocks.js';
import { TEST_STRATEGIES, EMPTY_STRATEGIES } from '../../fixtures/test-data.js';

test.describe('Strategies Page', () => {
  let strategiesPage;

  test.beforeEach(async ({ page }) => {
    strategiesPage = new StrategiesPage(page);
  });

  test.describe('Page Load', () => {
    test('should display page title and subtitle', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await strategiesPage.goto();

      await expect(strategiesPage.pageTitle).toBeVisible();
      await expect(strategiesPage.subtitle).toBeVisible();
    });

    test('should show loading state initially', async ({ page }) => {
      await mockApiWithDelay(page, 'strategies', TEST_STRATEGIES, 1000);

      await strategiesPage.goto();

      await expect(strategiesPage.loadingState).toBeVisible();
    });

    test('should display error state on API failure', async ({ page }) => {
      await mockApiError(page, 'strategies', 500, 'Server error');
      await strategiesPage.goto();

      await expect(strategiesPage.errorState).toBeVisible();
    });
  });

  test.describe('Strategy Cards', () => {
    test('should display grid of strategy cards', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      const count = await strategiesPage.getStrategyCount();
      expect(count).toBe(3);
    });

    test('should show strategy name on each card', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      await expect(page.locator('h3:has-text("random")')).toBeVisible();
      await expect(page.locator('h3:has-text("sentiment")')).toBeVisible();
      await expect(page.locator('h3:has-text("technical")')).toBeVisible();
    });

    test('should show strategy description', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      const description = await strategiesPage.getStrategyDescription('random');
      expect(description).toContain('Random signal generation');
    });

    test('should display asset type badges', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      const card = strategiesPage.getStrategyCard('random');
      await expect(card.locator('.bg-gray-100:has-text("crypto")')).toBeVisible();
      await expect(card.locator('.bg-gray-100:has-text("stock")')).toBeVisible();
    });

    test('should show provider information', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      const providerInfo = await strategiesPage.getProviderInfo('random');
      expect(providerInfo).toContain('random');
    });

    test('should have Run Backtest link with strategy param', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      const href = await strategiesPage.getRunBacktestHref('random');
      expect(href).toContain('strategy=random');
    });
  });

  test.describe('Navigation', () => {
    test('Run Backtest should navigate to new backtest form', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      await strategiesPage.clickRunBacktest('random');

      await expect(page).toHaveURL(/\/backtests\/new\?strategy=random/);
    });
  });

  test.describe('Empty State', () => {
    test('should show message when no strategies', async ({ page }) => {
      await mockStrategiesApi(page, EMPTY_STRATEGIES);
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      await expect(strategiesPage.emptyState).toBeVisible();
    });
  });

  test.describe('Responsive Layout', () => {
    test('should display cards in a grid layout', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      await expect(strategiesPage.strategiesGrid).toBeVisible();
    });
  });
});
