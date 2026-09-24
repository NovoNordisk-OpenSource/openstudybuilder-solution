import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './specs',
  fullyParallel: false,
  retries: 0,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  outputDir: '../../test-results/smoke',

  use: {
    baseURL: 'http://localhost:4173',
    headless: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },

  webServer: {
    command: 'npm run preview:demo',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
})
