import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Regression guard for a bug where NNTable's persisted column-layout snapshot
// raced the epoch columns being appended asynchronously, permanently hiding
// every epoch column behind the "arms"/"branches" defaults.
const SEED_STUDY_UID = 'Study_000001'

test('smoke: Design matrix renders epoch columns beyond the arm/branch defaults', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)

  const spy = setupConsoleSpy(page)

  await page.goto(`/studies/${SEED_STUDY_UID}/study_structure/design_matrix`)

  const table = page.locator('[data-cy="data-table"]')
  await expect(table).toBeVisible({ timeout: 20_000 })

  const headers = table.locator('thead th')
  await expect(headers.nth(2)).toBeVisible({ timeout: 20_000 })
  expect(await headers.count()).toBeGreaterThan(2)

  await expect(page.locator('[data-cy="table-export-button"]')).toBeVisible()

  spy.assertClean()
})
