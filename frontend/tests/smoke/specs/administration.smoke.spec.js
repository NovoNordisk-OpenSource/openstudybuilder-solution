import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

const ADMIN_PAGES = [
  ['Global preferences', '/administration/global-preferences'],
  ['Feature flags', '/administration/featureflags'],
  ['System announcements', '/administration/announcements'],
  ['Data completeness tags', '/administration/data-completeness-tags'],
  ['Complexity burdens', '/administration/complexity-burdens'],
  ['ODM vendor extensions', '/administration/odm-vendor-extensions'],
]

for (const [label, path] of ADMIN_PAGES) {
  test(`smoke: ${label} renders without crashes`, async ({ page }) => {
    await page.addInitScript(seedDemoAuth)

    const spy = setupConsoleSpy(page)

    await page.goto(path)

    await expect(
      page.locator('.page-title, .text-headline-large').first()
    ).toBeVisible({ timeout: 15_000 })

    spy.assertClean()
  })
}
