import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// The demo backend seeds 15 Studies flags and two Library flags
// ('compounds_library' and 'nsvs_library'), and every third flag has two
// versions (created switched off, later switched on). That is 20 versions for
// Studies and 3 for Library, of which 'nsvs_library' has two.
test('smoke: Feature flags history lists the versions of the selected section', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)

  const spy = setupConsoleSpy(page)

  await page.goto('/administration/featureflags')

  const button = page.locator('[data-cy="all-flags-history-button"]')
  const history = page.locator('[data-cy="version-history-window"]')

  // The button is icon only, and disabled until the flags are loaded.
  await expect(button).toHaveText('')
  await button.click()

  await expect(history).toBeVisible({ timeout: 20_000 })
  await expect(history.locator('tbody tr')).not.toHaveCount(0, {
    timeout: 20_000,
  })
  await expect(history).toContainText('History of studies feature flags')
  await expect(history.locator('thead th', { hasText: 'Section' })).toHaveCount(
    1
  )

  // The page opens on Studies, so the Library flag is not part of the history.
  // 20 versions come from one paginated request, 10 to a page.
  await expect(history.locator('tbody tr')).toHaveCount(10)
  await history.getByRole('button', { name: 'Next page' }).click()
  await expect(history.locator('tbody tr')).toHaveCount(10)
  await expect(
    history.locator('tbody tr', { hasText: 'nsvs_library' })
  ).toHaveCount(0)

  await history.locator('[data-cy="close-button"]').click()
  await expect(history).toBeHidden()

  // On the Library tab only the Library flags are listed. The two versions of
  // nsvs_library show Yes over No, and only the newer one flags the change.
  await page.getByRole('button', { name: 'Library', exact: true }).click()
  await button.click()
  await expect(history).toBeVisible({ timeout: 20_000 })
  await expect(history).toContainText('History of library feature flags')
  await expect(history.locator('tbody tr')).toHaveCount(3)
  const nsvs = history.locator('tbody tr', { hasText: 'nsvs_library' })
  await expect(nsvs).toHaveCount(2)
  await expect(nsvs.first()).toContainText('Yes')
  await expect(nsvs.last()).toContainText('No')
  await expect(nsvs.first().locator('.difference')).toHaveCount(1)
  await expect(nsvs.last().locator('.difference')).toHaveCount(0)

  await history.locator('[data-cy="close-button"]').click()
  await expect(history).toBeHidden()

  // Nothing is seeded in Admin, so there is no history to open.
  await page.getByRole('button', { name: 'Admin', exact: true }).click()
  await expect(button).toBeDisabled()

  spy.assertClean()
})
