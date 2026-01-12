/**
 * API mocking utilities for Playwright tests
 */

/**
 * Mock the strategies API endpoint
 * @param {import('@playwright/test').Page} page
 * @param {Object} data - Response data
 */
export async function mockStrategiesApi(page, data) {
  await page.route('**/api/strategies', (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data)
    });
  });
}

/**
 * Mock a single strategy endpoint
 * @param {import('@playwright/test').Page} page
 * @param {string} name - Strategy name
 * @param {Object} data - Response data
 */
export async function mockStrategyDetail(page, name, data) {
  await page.route(`**/api/strategies/${name}`, (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data)
    });
  });
}

/**
 * Mock the backtests list API endpoint
 * @param {import('@playwright/test').Page} page
 * @param {Object} data - Response data
 */
export async function mockBacktestsApi(page, data) {
  await page.route('**/api/backtests', (route) => {
    if (route.request().method() === 'GET') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data)
      });
    } else {
      route.continue();
    }
  });
}

/**
 * Mock creating a backtest
 * @param {import('@playwright/test').Page} page
 * @param {Object} response - Response data (should include backtest_id)
 */
export async function mockCreateBacktest(page, response) {
  await page.route('**/api/backtests', (route) => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    } else {
      route.continue();
    }
  });
}

/**
 * Mock a single backtest detail endpoint
 * @param {import('@playwright/test').Page} page
 * @param {number} id - Backtest ID
 * @param {Object} data - Response data
 */
export async function mockBacktestDetail(page, id, data) {
  await page.route(`**/api/backtests/${id}`, (route) => {
    if (route.request().method() === 'GET') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data)
      });
    } else {
      route.continue();
    }
  });
}

/**
 * Mock deleting a backtest
 * @param {import('@playwright/test').Page} page
 * @param {number} id - Backtest ID
 */
export async function mockDeleteBacktest(page, id) {
  await page.route(`**/api/backtests/${id}`, (route) => {
    if (route.request().method() === 'DELETE') {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Backtest deleted successfully' })
      });
    } else {
      route.continue();
    }
  });
}

/**
 * Mock canceling a backtest
 * @param {import('@playwright/test').Page} page
 * @param {number} id - Backtest ID
 */
export async function mockCancelBacktest(page, id) {
  await page.route(`**/api/backtests/${id}/cancel`, (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message: 'Backtest cancelled successfully' })
    });
  });
}

/**
 * Mock backtest results endpoint
 * @param {import('@playwright/test').Page} page
 * @param {number} id - Backtest ID
 * @param {Object} data - Response data with trades and daily_stats
 */
export async function mockBacktestResults(page, id, data) {
  await page.route(`**/api/results/${id}`, (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data)
    });
  });
}

/**
 * Mock trades endpoint with pagination
 * @param {import('@playwright/test').Page} page
 * @param {number} id - Backtest ID
 * @param {Object} data - Response data
 */
export async function mockBacktestTrades(page, id, data) {
  await page.route(`**/api/results/${id}/trades*`, (route) => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data)
    });
  });
}

/**
 * Mock an API error response
 * @param {import('@playwright/test').Page} page
 * @param {string} endpoint - API endpoint pattern (e.g., 'strategies', 'backtests')
 * @param {number} statusCode - HTTP status code
 * @param {string} detail - Error message
 */
export async function mockApiError(page, endpoint, statusCode, detail) {
  await page.route(`**/api/${endpoint}*`, (route) => {
    route.fulfill({
      status: statusCode,
      contentType: 'application/json',
      body: JSON.stringify({ detail })
    });
  });
}

/**
 * Mock network failure
 * @param {import('@playwright/test').Page} page
 * @param {string} endpoint - API endpoint pattern
 */
export async function mockNetworkError(page, endpoint) {
  await page.route(`**/api/${endpoint}*`, (route) => {
    route.abort('failed');
  });
}

/**
 * Mock API with delay (for testing loading states)
 * @param {import('@playwright/test').Page} page
 * @param {string} endpoint - API endpoint pattern
 * @param {Object} data - Response data
 * @param {number} delayMs - Delay in milliseconds
 */
export async function mockApiWithDelay(page, endpoint, data, delayMs = 1000) {
  await page.route(`**/api/${endpoint}*`, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, delayMs));
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(data)
    });
  });
}

/**
 * Mock health check endpoint
 * @param {import('@playwright/test').Page} page
 * @param {boolean} healthy - Whether the API is healthy
 */
export async function mockHealthCheck(page, healthy = true) {
  await page.route('**/health', (route) => {
    if (healthy) {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'healthy', database: 'connected' })
      });
    } else {
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'unhealthy', database: 'disconnected' })
      });
    }
  });
}

/**
 * Setup all common API mocks for a test
 * @param {import('@playwright/test').Page} page
 * @param {Object} options
 * @param {Object} options.strategies - Strategies data
 * @param {Object} options.backtests - Backtests data
 */
export async function setupMockedApi(page, { strategies, backtests } = {}) {
  if (strategies) {
    await mockStrategiesApi(page, strategies);
  }
  if (backtests) {
    await mockBacktestsApi(page, backtests);
  }
  await mockHealthCheck(page);
}
