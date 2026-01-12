import { test, expect } from '@playwright/test';
import { DashboardPage } from '../../pages/dashboard.page.js';
import { mockStrategiesApi, mockBacktestsApi, mockApiWithDelay } from '../../fixtures/api-mocks.js';
import { TEST_STRATEGIES, TEST_BACKTESTS, EMPTY_BACKTESTS } from '../../fixtures/test-data.js';

test.describe('Dashboard Page', () => {
  let dashboardPage;

  test.beforeEach(async ({ page }) => {
    dashboardPage = new DashboardPage(page);
  });

  test.describe('Page Load', () => {
    test('should display page title', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();

      await expect(dashboardPage.pageTitle).toBeVisible();
      await expect(dashboardPage.pageTitle).toHaveText('Dashboard');
    });

    test('should display header with navigation', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();

      await expect(dashboardPage.header).toBeVisible();
      await expect(dashboardPage.navDashboard).toBeVisible();
      await expect(dashboardPage.navStrategies).toBeVisible();
      await expect(dashboardPage.navBacktests).toBeVisible();
    });
  });

  test.describe('Stat Cards', () => {
    test('should display 4 stat cards', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      await expect(page.locator('text=Total Strategies')).toBeVisible();
      await expect(page.locator('text=Completed Backtests')).toBeVisible();
      await expect(page.locator('text=Running')).toBeVisible();
      await expect(page.locator('text=Avg Return')).toBeVisible();
    });

    test('should show correct strategy count', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      const value = await dashboardPage.getStatValue('Total Strategies');
      expect(value).toBe('3');
    });

    test('should show correct completed backtest count', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      const value = await dashboardPage.getStatValue('Completed Backtests');
      expect(value).toBe('2');
    });

    test('should show running backtest count', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      const value = await dashboardPage.getStatValue('Running');
      expect(value).toBe('1');
    });

    test('should calculate and display average return', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      const value = await dashboardPage.getStatValue('Avg Return');
      expect(value).toContain('%');
    });
  });

  test.describe('Recent Backtests Table', () => {
    test('should display table with correct columns', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      await expect(page.locator('th:has-text("Strategy")')).toBeVisible();
      await expect(page.locator('th:has-text("Asset")')).toBeVisible();
      await expect(page.locator('th:has-text("Return")')).toBeVisible();
      await expect(page.locator('th:has-text("Status")')).toBeVisible();
    });

    test('should display backtest entries', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      const count = await dashboardPage.getRecentBacktestsCount();
      expect(count).toBeGreaterThan(0);
    });

    test('should show status badges with correct styling', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      // Check for completed (green) badge
      await expect(page.locator('.bg-green-100').first()).toBeVisible();
    });

    test('should link strategy names to detail pages', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      const link = page.locator('tbody a').first();
      const href = await link.getAttribute('href');
      expect(href).toMatch(/\/backtests\/\d+/);
    });
  });

  test.describe('Empty State', () => {
    test('should display empty state when no backtests', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, EMPTY_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      await expect(dashboardPage.emptyState).toBeVisible();
    });

    test('should show link to run first backtest', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, EMPTY_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      await expect(dashboardPage.runFirstBacktestLink).toBeVisible();
    });
  });

  test.describe('Quick Action Cards', () => {
    test('should display 3 quick action cards', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      await expect(page.locator('h4:has-text("New Backtest")')).toBeVisible();
      await expect(page.locator('h4:has-text("View Strategies")')).toBeVisible();
      await expect(page.locator('h4:has-text("Compare Results")')).toBeVisible();
    });

    test('should navigate to new backtest page', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      await dashboardPage.clickNewBacktestQuickAction();
      await expect(page).toHaveURL(/\/backtests\/new/);
    });

    test('should navigate to strategies page', async ({ page }) => {
      await mockStrategiesApi(page, TEST_STRATEGIES);
      await mockBacktestsApi(page, TEST_BACKTESTS);
      await dashboardPage.goto();
      await dashboardPage.waitForApi();

      await dashboardPage.clickStrategiesQuickAction();
      await expect(page).toHaveURL('/strategies');
    });
  });

  test.describe('Auto-Refresh', () => {
    test('should poll for updates periodically', async ({ page }) => {
      let requestCount = 0;
      await page.route('**/api/backtests*', (route) => {
        requestCount++;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(TEST_BACKTESTS)
        });
      });
      await mockStrategiesApi(page, TEST_STRATEGIES);

      await dashboardPage.goto();

      // Wait for initial load + at least one refresh cycle (5 seconds)
      await page.waitForTimeout(6000);

      // Should have at least 2 requests (initial + 1 refresh)
      expect(requestCount).toBeGreaterThanOrEqual(2);
    });
  });
});
