import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

const PLACEHOLDER_UID = 'Demo_000001'

// Overviews use a placeholder UID; the mock backend's schema walker generates
// a synthetic response for most endpoints, but a few overview views read
// fields the walker leaves null (or hit components that crash on null
// subtrees). For those we add hand-handlers in src/demo/fixtures/library.js.
const OVERVIEW_PAGES = [
  [
    'Activity overview',
    `/library/activities/activities/${PLACEHOLDER_UID}/overview`,
  ],
  [
    'Activity instance overview',
    `/library/activities/activity-instances/${PLACEHOLDER_UID}/overview`,
  ],
  [
    'Activity instance class overview',
    `/library/activities/activity-instance-classes/${PLACEHOLDER_UID}/overview`,
  ],
  [
    'Activity instance parent class overview',
    `/library/activities/activity-instance-classes/${PLACEHOLDER_UID}/parent-class-overview`,
  ],
  [
    'Activity item class overview',
    `/library/activities/activity-item-classes/${PLACEHOLDER_UID}/overview`,
  ],
  [
    'Subgroup overview',
    `/library/activities/activity-sub-groups/${PLACEHOLDER_UID}/overview`,
  ],
  [
    'Group overview',
    `/library/activities/activity-groups/${PLACEHOLDER_UID}/overview`,
  ],
]

for (const [label, path] of OVERVIEW_PAGES) {
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
