import { test, expect } from '@playwright/test';
import { BacktestDetailPage } from '../../pages/backtest-detail.page.js';
import {
  mockBacktestDetail,
  mockBacktestResults,
  mockDeleteBacktest,
  mockCancelBacktest,
  mockApiError
} from '../../fixtures/api-mocks.js';
import { COMPLETED_BACKTEST, RUNNING_BACKTEST, BACKTEST_RESULTS } from '../../fixtures/test-data.js';

test.describe('Backtest Detail Page', () => {
  let detailPage;

  test.beforeEach(async ({ page }) => {
    detailPage = new BacktestDetailPage(page);
  });

  test.describe('Header Section', () => {
    test('should display strategy name', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      const name = await detailPage.getStrategyName();
      expect(name).toContain('random');
    });

    test('should display status badge for completed backtest', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      const status = await detailPage.getStatus();
      expect(status.toLowerCase()).toBe('completed');
    });

    test('should display status badge for running backtest', async ({ page }) => {
      await mockBacktestDetail(page, 2, RUNNING_BACKTEST);
      await detailPage.goto(2);
      await detailPage.waitForApi();

      expect(await detailPage.isRunning()).toBe(true);
    });
  });

  test.describe('Action Buttons', () => {
    test('should show Cancel button for running backtest', async ({ page }) => {
      await mockBacktestDetail(page, 2, RUNNING_BACKTEST);
      await detailPage.goto(2);
      await detailPage.waitForApi();

      expect(await detailPage.isCancelVisible()).toBe(true);
    });

    test('should hide Cancel button for completed backtest', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      expect(await detailPage.isCancelVisible()).toBe(false);
    });

    test('should always show Delete button', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      await expect(detailPage.deleteButton).toBeVisible();
    });

    test('should show back link', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      await expect(detailPage.backLink).toBeVisible();
    });
  });

  test.describe('Metrics Cards', () => {
    test('should display all 8 metric cards', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      expect(await detailPage.hasAllMetrics()).toBe(true);
    });

    test('should show correct total return value', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      const returnValue = await detailPage.getTotalReturn();
      expect(returnValue).toContain('15');
    });

    test('should show positive return in green', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      expect(await detailPage.isReturnPositive()).toBe(true);
    });

    test('should format currency values correctly', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      const initialCash = await detailPage.getMetricValue('Initial Cash');
      expect(initialCash).toContain('100');
    });
  });

  test.describe('Equity Curve Chart', () => {
    test('should display chart for completed backtest', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      await expect(page.locator('text=Equity Curve')).toBeVisible();
      expect(await detailPage.isChartVisible()).toBe(true);
    });

    test('should not show chart when no daily stats', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, { ...BACKTEST_RESULTS, daily_stats: [] });
      await detailPage.goto(1);
      await detailPage.waitForApi();

      expect(await detailPage.isChartVisible()).toBe(false);
    });
  });

  test.describe('Trades Table', () => {
    test('should display trades table', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      await expect(page.locator('text=Trades')).toBeVisible();
      await expect(detailPage.tradesTable).toBeVisible();
    });

    test('should display correct number of trades', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      const count = await detailPage.getTradeCount();
      expect(count).toBe(5);
    });

    test('should color BUY trades green', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      expect(await detailPage.hasBuyTrades()).toBe(true);
    });

    test('should color SELL trades red', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      expect(await detailPage.hasSellTrades()).toBe(true);
    });
  });

  test.describe('Cancel Action', () => {
    test('should cancel running backtest', async ({ page }) => {
      await mockBacktestDetail(page, 2, RUNNING_BACKTEST);
      await mockCancelBacktest(page, 2);

      await detailPage.goto(2);
      await detailPage.waitForApi();

      await detailPage.clickCancel();

      // Should trigger the cancel API call
      // The page would refresh with new status
    });
  });

  test.describe('Delete Action', () => {
    test('should delete backtest and redirect', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await mockDeleteBacktest(page, 1);

      await detailPage.goto(1);
      await detailPage.waitForApi();

      await detailPage.confirmDelete();

      await expect(page).toHaveURL('/backtests');
    });
  });

  test.describe('Navigation', () => {
    test('should navigate back to backtests list', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await detailPage.goto(1);
      await detailPage.waitForApi();

      await detailPage.goBack();

      await expect(page).toHaveURL('/backtests');
    });
  });

  test.describe('Error Handling', () => {
    test('should show error for non-existent backtest', async ({ page }) => {
      await mockApiError(page, 'backtests/999', 404, 'Backtest not found');
      await detailPage.goto(999);

      expect(await detailPage.hasError()).toBe(true);
    });
  });

  test.describe('Auto-Refresh for Running', () => {
    test('should poll for updates when running', async ({ page }) => {
      let pollCount = 0;
      await page.route('**/api/backtests/2', (route) => {
        pollCount++;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(RUNNING_BACKTEST)
        });
      });

      await detailPage.goto(2);
      await page.waitForTimeout(5000);

      expect(pollCount).toBeGreaterThan(1);
    });

    test('should stop polling when completed', async ({ page }) => {
      let pollCount = 0;
      await page.route('**/api/backtests/1', (route) => {
        pollCount++;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(COMPLETED_BACKTEST)
        });
      });
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);

      await detailPage.goto(1);
      await page.waitForTimeout(5000);

      // Should have initial load but minimal polling for completed backtest
      expect(pollCount).toBeLessThanOrEqual(3);
    });
  });
});
