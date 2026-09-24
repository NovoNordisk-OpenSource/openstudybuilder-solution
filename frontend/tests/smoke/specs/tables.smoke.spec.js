import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Each entry is a route whose primary v-data-table should hold at least one
// data row in demo mode. Catches "the demo paginated wrapper changed shape and
// the table silently empties" regressions that smoke-without-row-assertions
// would miss.
const TABLE_ROUTES = [
  ['Sponsor codelists', '/library/sponsor'],
  ['Activities', '/library/activities/activities'],
  ['Activity instances', '/library/activities/activity-instances'],
  ['Activity item classes', '/library/activities/activity-item-classes'],
  [
    'Activity instance classes',
    '/library/activities/activity-instance-classes',
  ],
  ['Units', '/library/units'],
  ['CT catalogues', '/library/ct_catalogues'],
  ['Compounds', '/library/interventions/compounds'],
  ['Endpoint instances', '/library/endpoints'],
  ['Criteria instances', '/library/criteria_instances'],
]

for (const [label, path] of TABLE_ROUTES) {
  test(`smoke: ${label} table loads at least one data row`, async ({
    page,
  }) => {
    await page.addInitScript(seedDemoAuth)

    const spy = setupConsoleSpy(page)

    await page.goto(path)

    const dataRows = page.locator(
      '.v-data-table tbody tr:not(.v-data-table-rows-no-data):not(.v-data-table-rows-loading)'
    )

    await expect(dataRows.first()).toBeVisible({ timeout: 20_000 })
    expect(await dataRows.count()).toBeGreaterThan(0)

    spy.assertClean()
  })
}
