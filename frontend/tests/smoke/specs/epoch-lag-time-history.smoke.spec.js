import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Regression guard for a bug where the epoch version history printed the lag
// time value without its unit, so an edit that only swapped days for weeks
// produced two identical rows.
const SEED_STUDY_UID = 'Study_000001'

test('smoke: Epoch version history shows the lag time unit and flags a unit-only edit', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)

  const spy = setupConsoleSpy(page)

  await page.goto(`/studies/${SEED_STUDY_UID}/study_structure/epochs`)

  await expect(page.locator('[data-cy="data-table"]')).toBeVisible({
    timeout: 20_000,
  })

  // An empty epoch list would fail on the action button with a confusing
  // "no elements" error, so assert the rows arrived first.
  await expect(page.locator('[data-cy="data-table"] tbody tr')).not.toHaveCount(
    0,
    { timeout: 20_000 }
  )

  await page.locator('[data-cy="table-item-action-button"]').first().click()
  await page.getByRole('listitem').filter({ hasText: 'History' }).click()

  const history = page.locator('[data-cy="version-history-window"]')
  await expect(history).toBeVisible({ timeout: 20_000 })

  await expect(history.locator('tbody tr')).toHaveCount(2)
  await expect(history.locator('tbody tr').first()).toContainText('32 weeks')
  await expect(history.locator('tbody tr').nth(1)).toContainText('32 days')

  // Lag time reads as one value, so the unit never gets its own column.
  await expect(
    history.locator('thead th', { hasText: 'lag time unit' })
  ).toHaveCount(0)

  await expect(history.locator('tbody td .difference')).toHaveCount(1)
  await expect(history.locator('tbody td .difference')).toHaveText('32 weeks')

  spy.assertClean()
})
