import { defineConfig, devices } from '@playwright/test';

// Server configuration with fallback support
const API_PORT = process.env.API_PORT || 8847;
const WEB_PORT = process.env.WEB_PORT || 3847;

// Base URLs - can be overridden via environment variables
const baseURL = process.env.BASE_URL || `http://localhost:${WEB_PORT}`;

// Check if we should skip starting servers (for when they're already running)
const SKIP_SERVER_START = process.env.SKIP_SERVER_START === 'true';

export default defineConfig({
  testDir: './tests',
  timeout: 30000,
  expect: {
    timeout: 5000
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    process.env.CI ? ['github'] : ['list']
  ],

  use: {
    baseURL: baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  // Global setup for server detection (optional)
  globalSetup: SKIP_SERVER_START ? undefined : './helpers/global-setup.js',

  projects: [
    {
      name: 'smoke',
      testMatch: /smoke\.spec\.js/,
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testIgnore: /smoke\.spec\.js/,
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      testIgnore: [/smoke\.spec\.js/, /flow\.spec\.js/],
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
      testIgnore: [/smoke\.spec\.js/, /flow\.spec\.js/],
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
      testMatch: /pages\/.*\.spec\.js/,
    },
    {
      name: 'api-integration',
      testMatch: /integration\/.*\.spec\.js/,
      use: {
        ...devices['Desktop Chrome'],
        baseURL: baseURL,
      },
    },
  ],

  // Web server configuration
  // Playwright will reuse existing servers if they're already running
  webServer: SKIP_SERVER_START ? undefined : [
    {
      command: `cd ../../.. && uv run uvicorn trading_lab.api.main:app --host 0.0.0.0 --port ${API_PORT}`,
      port: parseInt(API_PORT),
      timeout: 120000,
      reuseExistingServer: true,
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: `cd .. && npm run dev -- --port ${WEB_PORT}`,
      port: parseInt(WEB_PORT),
      timeout: 120000,
      reuseExistingServer: true,
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});
