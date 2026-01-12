import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/dashboard.page.js';
import { StrategiesPage } from '../../pages/strategies.page.js';
import { NewBacktestPage } from '../../pages/new-backtest.page.js';
import { BacktestDetailPage } from '../../pages/backtest-detail.page.js';
import {
  mockStrategiesApi,
  mockBacktestsApi,
  mockCreateBacktest,
  mockBacktestDetail,
  mockBacktestResults
} from '../../fixtures/api-mocks.js';
import {
  TEST_STRATEGIES,
  TEST_BACKTESTS,
  CREATE_BACKTEST_RESPONSE,
  COMPLETED_BACKTEST,
  BACKTEST_RESULTS
} from '../../fixtures/test-data.js';

test.describe('Create Backtest Flow', () => {
  test.describe('Happy Path - From Dashboard', () => {
    test('complete flow: dashboard -> new backtest -> fill form -> view detail', async ({ page }) => {
      // Setup mocks
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockCreateBacktest(page, CREATE_BACKTEST_RESPONSE);
      await mockBacktestDetail(page, CREATE_BACKTEST_RESPONSE.backtest_id, {
        ...COMPLETED_BACKTEST,
        id: CREATE_BACKTEST_RESPONSE.backtest_id,
        status: 'pending'
      });

      const dashboardPage = new DashboardPage(page);
      const newBacktestPage = new NewBacktestPage(page);
      const detailPage = new BacktestDetailPage(page);

      // Start at dashboard
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      // Click New Backtest from header
      await dashboardPage.goToNewBacktest();
      await expect(page).toHaveURL(/\/backtests\/new/);

      // Fill form
      await newBacktestPage.waitForApi();
      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.setAsset('ETH/USD');
      await newBacktestPage.setDateRange('2024-01-01', '2024-03-31');
      await newBacktestPage.setInitialCash(50000);

      // Submit
      await newBacktestPage.submit();

      // Should redirect to detail page
      await expect(page).toHaveURL(`/backtests/${CREATE_BACKTEST_RESPONSE.backtest_id}`);

      // Should show the backtest details
      await expect(page.locator('h1')).toBeVisible();
    });

    test('complete flow via quick action card', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockCreateBacktest(page, CREATE_BACKTEST_RESPONSE);
      await mockBacktestDetail(page, CREATE_BACKTEST_RESPONSE.backtest_id, {
        ...COMPLETED_BACKTEST,
        id: CREATE_BACKTEST_RESPONSE.backtest_id,
        status: 'pending'
      });

      const dashboardPage = new DashboardPage(page);
      const newBacktestPage = new NewBacktestPage(page);

      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      // Click quick action card
      await dashboardPage.clickNewBacktestQuickAction();
      await expect(page).toHaveURL(/\/backtests\/new/);

      // Fill minimal form
      await newBacktestPage.waitForApi();
      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.submit();

      await expect(page).toHaveURL(`/backtests/${CREATE_BACKTEST_RESPONSE.backtest_id}`);
    });
  });

  test.describe('Happy Path - From Strategy Card', () => {
    test('flow: strategies page -> Run Backtest -> pre-filled form -> submit', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockCreateBacktest(page, CREATE_BACKTEST_RESPONSE);
      await mockBacktestDetail(page, CREATE_BACKTEST_RESPONSE.backtest_id, {
        ...COMPLETED_BACKTEST,
        id: CREATE_BACKTEST_RESPONSE.backtest_id,
        status: 'pending'
      });

      const strategiesPage = new StrategiesPage(page);
      const newBacktestPage = new NewBacktestPage(page);

      // Go to strategies page
      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      // Click Run Backtest on a strategy
      await strategiesPage.clickRunBacktest('random');
      await expect(page).toHaveURL(/\/backtests\/new\?strategy=random/);

      // Strategy should be pre-selected
      await newBacktestPage.waitForApi();
      const selected = await newBacktestPage.getSelectedStrategy();
      expect(selected).toBe('random');

      // Submit directly
      await newBacktestPage.submit();
      await expect(page).toHaveURL(`/backtests/${CREATE_BACKTEST_RESPONSE.backtest_id}`);
    });

    test('should pre-fill correct strategy from sentiment card', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);

      const strategiesPage = new StrategiesPage(page);
      const newBacktestPage = new NewBacktestPage(page);

      await strategiesPage.goto();
      await strategiesPage.waitForApi();

      await strategiesPage.clickRunBacktest('sentiment');

      await newBacktestPage.waitForApi();
      const selected = await newBacktestPage.getSelectedStrategy();
      expect(selected).toBe('sentiment');
    });
  });

  test.describe('Error Cases', () => {
    test('should handle network error gracefully', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await page.route('**/api/backtests', (route) => {
        if (route.request().method() === 'POST') {
          route.abort('failed');
        } else {
          route.continue();
        }
      });

      const newBacktestPage = new NewBacktestPage(page);

      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.submit();

      expect(await newBacktestPage.hasError()).toBe(true);
    });

    test('should handle validation error from API', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await page.route('**/api/backtests', (route) => {
        if (route.request().method() === 'POST') {
          route.fulfill({
            status: 422,
            contentType: 'application/json',
            body: JSON.stringify({
              detail: 'End date must be after start date'
            })
          });
        } else {
          route.continue();
        }
      });

      const newBacktestPage = new NewBacktestPage(page);

      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.setDateRange('2024-06-01', '2024-01-01');
      await newBacktestPage.submit();

      expect(await newBacktestPage.hasError()).toBe(true);
      const error = await newBacktestPage.getErrorMessage();
      expect(error).toContain('End date must be after start date');
    });

    test('should handle server error', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await page.route('**/api/backtests', (route) => {
        if (route.request().method() === 'POST') {
          route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({
              detail: 'Internal server error'
            })
          });
        } else {
          route.continue();
        }
      });

      const newBacktestPage = new NewBacktestPage(page);

      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.submit();

      expect(await newBacktestPage.hasError()).toBe(true);
    });
  });

  test.describe('Form State Preservation', () => {
    test('should preserve form data when switching asset types', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);

      const newBacktestPage = new NewBacktestPage(page);

      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      // Fill some fields
      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.setAsset('AAPL');
      await newBacktestPage.setInitialCash(75000);

      // Switch asset type
      await newBacktestPage.selectAssetType('stock');

      // Verify other fields are preserved
      expect(await newBacktestPage.getSelectedStrategy()).toBe('random');
      expect(await newBacktestPage.assetInput.inputValue()).toBe('AAPL');
      expect(await newBacktestPage.initialCashInput.inputValue()).toBe('75000');
    });
  });

  test.describe('Cancel Flow', () => {
    test('should return to previous page on cancel', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);

      // Start from backtests list
      await page.goto('/backtests');
      await page.waitForLoadState('networkidle');

      // Go to new backtest
      await page.getByRole('link', { name: 'New Backtest' }).first().click();
      await expect(page).toHaveURL('/backtests/new');

      // Cancel
      await page.getByRole('button', { name: 'Cancel' }).click();

      // Should go back
      await expect(page).toHaveURL('/backtests');
    });
  });
});
