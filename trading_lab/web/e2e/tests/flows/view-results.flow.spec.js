import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/dashboard.page.js';
import { BacktestsPage } from '../../pages/backtests.page.js';
import { BacktestDetailPage } from '../../pages/backtest-detail.page.js';
import {
  mockStrategiesApi,
  mockBacktestsApi,
  mockBacktestDetail,
  mockBacktestResults,
  mockDeleteBacktest
} from '../../fixtures/api-mocks.js';
import {
  TEST_STRATEGIES,
  TEST_BACKTESTS,
  COMPLETED_BACKTEST,
  RUNNING_BACKTEST,
  BACKTEST_RESULTS
} from '../../fixtures/test-data.js';

test.describe('View Results Flow', () => {
  test.describe('From Dashboard', () => {
    test('navigate from dashboard to completed backtest and view all details', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);

      const dashboardPage = new DashboardPage(page);
      const detailPage = new BacktestDetailPage(page);

      // Start at dashboard
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      // Click on first backtest in recent table
      await dashboardPage.clickRecentBacktest('random');

      // Should be on detail page
      await expect(page).toHaveURL('/backtests/1');

      // Verify all sections are visible
      expect(await detailPage.hasAllMetrics()).toBe(true);
      await expect(page.locator('text=Equity Curve')).toBeVisible();
      await expect(page.locator('text=Trades')).toBeVisible();

      // Verify chart is displayed
      expect(await detailPage.isChartVisible()).toBe(true);

      // Verify trades are displayed
      const tradeCount = await detailPage.getTradeCount();
      expect(tradeCount).toBeGreaterThan(0);
    });
  });

  test.describe('From Backtests List', () => {
    test('navigate from backtests list to detail page', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);

      const backtestsPage = new BacktestsPage(page);
      const detailPage = new BacktestDetailPage(page);

      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      await backtestsPage.clickBacktest('random');

      await expect(page).toHaveURL('/backtests/1');
      expect(await detailPage.isCompleted()).toBe(true);
    });

    test('view different status backtests', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockBacktestDetail(page, 2, RUNNING_BACKTEST);

      const backtestsPage = new BacktestsPage(page);
      const detailPage = new BacktestDetailPage(page);

      await backtestsPage.goto();
      await backtestsPage.waitForApi();

      // Click on a running backtest
      const runningRow = page.locator('tr').filter({ hasText: 'running' }).first();
      await runningRow.locator('a').first().click();

      expect(await detailPage.isRunning()).toBe(true);
      expect(await detailPage.isCancelVisible()).toBe(true);
    });
  });

  test.describe('Running Backtest Updates', () => {
    test('should update when backtest completes', async ({ page }) => {
      let requestCount = 0;
      const runningState = { ...RUNNING_BACKTEST };
      const completedState = { ...COMPLETED_BACKTEST, id: 2 };

      await page.route('**/api/backtests/2', (route) => {
        requestCount++;
        // After 3 requests, return completed status
        const response = requestCount >= 3 ? completedState : runningState;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(response)
        });
      });
      await mockBacktestResults(page, 2, { ...BACKTEST_RESULTS, backtest: completedState });

      const detailPage = new BacktestDetailPage(page);

      await detailPage.goto(2);

      // Initially running
      await expect(page.locator('text=running')).toBeVisible();

      // Wait for status to change (polling should update it)
      await expect(page.locator('text=completed')).toBeVisible({ timeout: 15000 });
    });
  });

  test.describe('Navigation Back', () => {
    test('should navigate back to backtests list', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);

      const detailPage = new BacktestDetailPage(page);

      await detailPage.goto(1);
      await detailPage.waitForApi();

      await detailPage.goBack();

      await expect(page).toHaveURL('/backtests');
    });
  });

  test.describe('Delete Flow', () => {
    test('should delete and redirect to list', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);
      await mockDeleteBacktest(page, 1);

      const detailPage = new BacktestDetailPage(page);

      await detailPage.goto(1);
      await detailPage.waitForApi();

      await detailPage.confirmDelete();

      await expect(page).toHaveURL('/backtests');
    });

    test('should cancel delete when dismissed', async ({ page }) => {
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);

      const detailPage = new BacktestDetailPage(page);

      await detailPage.goto(1);
      await detailPage.waitForApi();

      await detailPage.cancelDelete();

      // Should still be on detail page
      await expect(page).toHaveURL('/backtests/1');
    });
  });

  test.describe('Metrics Analysis', () => {
    test('should display correct metric values', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);

      const detailPage = new BacktestDetailPage(page);

      await detailPage.goto(1);
      await detailPage.waitForApi();

      // Check specific metrics
      const totalReturn = await detailPage.getTotalReturn();
      expect(totalReturn).toContain('15');

      const winRate = await detailPage.getMetricValue('Win Rate');
      expect(winRate).toContain('65');

      const sharpe = await detailPage.getMetricValue('Sharpe Ratio');
      expect(sharpe).toContain('1.4');
    });

    test('should show return color based on value', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);

      const detailPage = new BacktestDetailPage(page);

      await detailPage.goto(1);
      await detailPage.waitForApi();

      // Positive return should be green
      expect(await detailPage.isReturnPositive()).toBe(true);
      expect(await detailPage.isReturnNegative()).toBe(false);
    });
  });

  test.describe('Trades Analysis', () => {
    test('should display trade details', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);

      const detailPage = new BacktestDetailPage(page);

      await detailPage.goto(1);
      await detailPage.waitForApi();

      // Verify trade info
      const firstTrade = await detailPage.getTradeInfo(0);
      expect(firstTrade.side).toContain('BUY');
      expect(firstTrade.quantity).toBeTruthy();
      expect(firstTrade.price).toBeTruthy();
    });

    test('should distinguish buy and sell trades visually', async ({ page }) => {
      await mockBacktestDetail(page, 1, COMPLETED_BACKTEST);
      await mockBacktestResults(page, 1, BACKTEST_RESULTS);

      const detailPage = new BacktestDetailPage(page);

      await detailPage.goto(1);
      await detailPage.waitForApi();

      expect(await detailPage.hasBuyTrades()).toBe(true);
      expect(await detailPage.hasSellTrades()).toBe(true);
    });
  });
});
