import { test, expect } from '@playwright/test';
import { NewBacktestPage } from '../../pages/new-backtest.page.js';
import { mockStrategiesApi, mockCreateBacktest, mockApiError } from '../../fixtures/api-mocks.js';
import { TEST_STRATEGIES, VALID_BACKTEST_FORM, CREATE_BACKTEST_RESPONSE } from '../../fixtures/test-data.js';

test.describe('New Backtest Page', () => {
  let newBacktestPage;

  test.beforeEach(async ({ page }) => {
    newBacktestPage = new NewBacktestPage(page);
    await mockStrategiesApi(page, TEST_STRATEGIES);
  });

  test.describe('Form Fields', () => {
    test('should display all required form fields', async ({ page }) => {
      await newBacktestPage.goto();

      expect(await newBacktestPage.hasAllFields()).toBe(true);
    });

    test('should display page title', async ({ page }) => {
      await newBacktestPage.goto();

      await expect(newBacktestPage.pageTitle).toBeVisible();
    });

    test('should populate strategy dropdown from API', async ({ page }) => {
      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      const strategies = await newBacktestPage.getAvailableStrategies();
      expect(strategies).toContain('random');
      expect(strategies).toContain('sentiment');
      expect(strategies).toContain('technical');
    });

    test('should have correct default values', async ({ page }) => {
      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      const defaults = await newBacktestPage.getFormDefaults();
      expect(defaults.asset).toBe('BTC/USD');
      expect(defaults.asset_type).toBe('crypto');
      expect(defaults.initial_cash).toBe('100000');
    });
  });

  test.describe('Strategy Pre-selection', () => {
    test('should pre-select strategy from URL param', async ({ page }) => {
      await newBacktestPage.goto('random');
      await newBacktestPage.waitForApi();

      const selected = await newBacktestPage.getSelectedStrategy();
      expect(selected).toBe('random');
    });

    test('should pre-select different strategy from URL', async ({ page }) => {
      await newBacktestPage.goto('sentiment');
      await newBacktestPage.waitForApi();

      const selected = await newBacktestPage.getSelectedStrategy();
      expect(selected).toBe('sentiment');
    });
  });

  test.describe('Asset Type Behavior', () => {
    test('should show exchange dropdown for crypto', async ({ page }) => {
      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      // Default is crypto
      expect(await newBacktestPage.isExchangeVisible()).toBe(true);
    });

    test('should hide exchange dropdown for stock', async ({ page }) => {
      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectAssetType('stock');

      expect(await newBacktestPage.isExchangeVisible()).toBe(false);
    });

    test('should hide exchange dropdown for forex', async ({ page }) => {
      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectAssetType('forex');

      expect(await newBacktestPage.isExchangeVisible()).toBe(false);
    });

    test('should show exchange again when switching back to crypto', async ({ page }) => {
      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectAssetType('stock');
      expect(await newBacktestPage.isExchangeVisible()).toBe(false);

      await newBacktestPage.selectAssetType('crypto');
      expect(await newBacktestPage.isExchangeVisible()).toBe(true);
    });
  });

  test.describe('Form Submission', () => {
    test('should submit form and redirect on success', async ({ page }) => {
      await mockCreateBacktest(page, CREATE_BACKTEST_RESPONSE);
      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.submit();

      await expect(page).toHaveURL(`/backtests/${CREATE_BACKTEST_RESPONSE.backtest_id}`);
    });

    test('should show loading state during submission', async ({ page }) => {
      await page.route('**/api/backtests', async (route) => {
        if (route.request().method() === 'POST') {
          await new Promise((r) => setTimeout(r, 500));
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(CREATE_BACKTEST_RESPONSE)
          });
        } else {
          route.continue();
        }
      });

      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.submit();

      await expect(newBacktestPage.loadingButton).toBeVisible();
      expect(await newBacktestPage.isSubmitting()).toBe(true);
    });

    test('should disable submit button during submission', async ({ page }) => {
      await page.route('**/api/backtests', async (route) => {
        if (route.request().method() === 'POST') {
          await new Promise((r) => setTimeout(r, 1000));
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(CREATE_BACKTEST_RESPONSE)
          });
        } else {
          route.continue();
        }
      });

      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.submit();

      // Button should be in loading state and disabled
      await expect(newBacktestPage.loadingButton).toBeDisabled();
    });
  });

  test.describe('Error Handling', () => {
    test('should display error message on API failure', async ({ page }) => {
      await page.route('**/api/backtests', (route) => {
        if (route.request().method() === 'POST') {
          route.fulfill({
            status: 422,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Invalid strategy name' })
          });
        } else {
          route.continue();
        }
      });

      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.submit();

      expect(await newBacktestPage.hasError()).toBe(true);
      const errorText = await newBacktestPage.getErrorMessage();
      expect(errorText).toContain('Invalid strategy name');
    });

    test('should handle network errors gracefully', async ({ page }) => {
      await page.route('**/api/backtests', (route) => {
        if (route.request().method() === 'POST') {
          route.abort('failed');
        } else {
          route.continue();
        }
      });

      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.selectStrategy('random');
      await newBacktestPage.submit();

      expect(await newBacktestPage.hasError()).toBe(true);
    });
  });

  test.describe('Form Validation', () => {
    test('should require strategy selection', async ({ page }) => {
      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      // Check that strategy select has required attribute
      const required = await newBacktestPage.strategySelect.getAttribute('required');
      expect(required).not.toBeNull();
    });

    test('should allow filling all form fields', async ({ page }) => {
      await newBacktestPage.goto();
      await newBacktestPage.waitForApi();

      await newBacktestPage.fillForm(VALID_BACKTEST_FORM);

      expect(await newBacktestPage.getSelectedStrategy()).toBe('random');
      expect(await newBacktestPage.assetInput.inputValue()).toBe('BTC/USD');
    });
  });

  test.describe('Cancel Button', () => {
    test('should navigate back on cancel', async ({ page }) => {
      await newBacktestPage.goto();
      await page.goto('/backtests');
      await page.waitForLoadState('networkidle');

      await page.getByRole('link', { name: 'New Backtest' }).first().click();
      await expect(page).toHaveURL('/backtests/new');

      await newBacktestPage.cancel();

      await expect(page).toHaveURL('/backtests');
    });
  });

  test.describe('Submit and Cancel Buttons', () => {
    test('should display both buttons', async ({ page }) => {
      await newBacktestPage.goto();

      await expect(newBacktestPage.submitButton).toBeVisible();
      await expect(newBacktestPage.cancelButton).toBeVisible();
    });
  });
});
