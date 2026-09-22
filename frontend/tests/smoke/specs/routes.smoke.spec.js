import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

const ROUTES = [
  ['Home', '/', 'h1'],
  ['Studies Summary', '/studies/summary', 'h1.text-display-medium'],
  ['Studies SelectOrAdd', '/studies/select_or_add_study', '.page-title'],
  ['Library Summary', '/library/summary', 'h1.text-display-medium'],
  ['Library Activities', '/library/activities', '.page-title'],
  ['Library CRF Viewer', '/library/crf-viewer', '.page-title'],
]

for (const [label, path, stableSelector] of ROUTES) {
  test(`smoke: ${label} renders without crashes`, async ({ page }) => {
    await page.addInitScript(seedDemoAuth)

    const spy = setupConsoleSpy(page)

    await page.goto(path)

    await expect(page.locator(stableSelector).first()).toBeVisible({
      timeout: 15_000,
    })

    spy.assertClean()
  })
}
