import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Vuetify teleports each v-select's option list into a page-level overlay,
// and several of those overlays can be mounted (though hidden) at once for
// a form with multiple selects. `page.getByRole('option')` matches across
// all of them regardless of visibility, so a plain index-based click can
// silently land on the wrong select's — or a hidden — option. Scoping to
// the menu id from the trigger's own aria-controls avoids that ambiguity
// and is what actually made this test's selections reliable.
async function openScopedMenu(page, trigger) {
  await trigger.click()
  const menuId = await trigger
    .locator('[role="combobox"]')
    .first()
    .getAttribute('aria-controls')
  const options = page.locator(`#${menuId} [role="option"]`)
  await expect(options.first()).toBeVisible({ timeout: 10_000 })
  return options
}

async function openNsvForm(page) {
  await page.addInitScript(seedDemoAuth)
  await page.goto('/library/activities/non-standard-variables')
  const addButton = page
    .locator('[data-cy="add-non-standard-variable"]')
    .first()
  await expect(addButton).toBeVisible({ timeout: 15_000 })
  await addButton.click()
  const dialog = page
    .locator('[role="dialog"]:visible')
    .filter({ has: page.locator('[data-cy="cancel-button"]') })
    .first()
  await expect(dialog).toBeVisible({ timeout: 10_000 })
  return dialog
}

test('smoke: NSV form shows CT Term info and disables codelist search until CT Term', async ({
  page,
}) => {
  const spy = setupConsoleSpy(page)
  const dialog = await openNsvForm(page)

  const info = dialog.locator('[data-cy="nsv-codelist-info"]')
  await expect(info).toBeVisible()
  await info.hover()
  await expect(
    page.getByText('Select Data Type CT Term to choose a codelist.')
  ).toBeVisible({ timeout: 5_000 })

  const searchButton = dialog.locator('[data-cy="nsv-codelist-search"]')
  await expect(searchButton).toBeDisabled()

  await dialog.locator('[data-cy="nsv-data-type"]').click()
  const ctTermOption = page.getByRole('option', { name: /ct\s*term/i }).first()
  await expect(ctTermOption).toBeVisible({ timeout: 10_000 })
  await ctTermOption.click()
  await expect(searchButton).toBeEnabled()
  await searchButton.click()
  const picker = page
    .locator('[role="dialog"]:visible')
    .filter({ has: page.locator('[data-cy="nsv-codelist-search-field"]') })
    .first()
  await expect(picker).toBeVisible({ timeout: 10_000 })
  const firstRow = picker.locator('[data-cy^="nsv-codelist-row-"]').first()
  await expect(firstRow).toBeVisible({ timeout: 10_000 })
  await firstRow.click()
  await picker.getByRole('button', { name: /save/i }).click()
  await expect(
    dialog.locator('[data-cy="nsv-codelist-code"] input')
  ).not.toHaveValue('')

  await dialog.locator('[data-cy="cancel-button"]').click()
  spy.assertClean()
})

test('smoke: NSV CDISC defined switch is visible and form cancels', async ({
  page,
}) => {
  const spy = setupConsoleSpy(page)
  const dialog = await openNsvForm(page)
  await expect(dialog.locator('[data-cy="nsv-is-cdisc-defined"]')).toBeVisible()
  await dialog.locator('[data-cy="cancel-button"]').click()
  await expect(page.locator('[role="dialog"]:visible')).toHaveCount(0, {
    timeout: 5_000,
  })
  spy.assertClean()
})

test('smoke: Allow for multiple toggles Activity Instance Class to multi-select', async ({
  page,
}) => {
  const spy = setupConsoleSpy(page)
  const dialog = await openNsvForm(page)
  const aic = dialog.locator('[data-cy="nsv-activity-instance-class"]')
  await expect(aic).toBeVisible()
  await expect(aic).not.toHaveClass(/v-select--multiple/)

  await dialog
    .locator('[data-cy="nsv-is-multiple"] input')
    .click({ force: true })
  await expect(aic).toHaveClass(/v-select--multiple/)

  await dialog.locator('[data-cy="cancel-button"]').click()
  spy.assertClean()
})

test('smoke: multi-select Activity Instance Classes are all sent on create', async ({
  page,
}) => {
  const spy = setupConsoleSpy(page)
  const dialog = await openNsvForm(page)

  await dialog
    .locator('[data-cy="nsv-is-multiple"] input')
    .click({ force: true })
  const aic = dialog.locator('[data-cy="nsv-activity-instance-class"]')
  const aicOptions = await openScopedMenu(page, aic)
  await aicOptions.nth(0).click()
  await expect(aic.locator('.v-chip')).toHaveCount(1, { timeout: 10_000 })
  await aicOptions.nth(1).click()
  await expect(aic.locator('.v-chip')).toHaveCount(2, { timeout: 10_000 })
  await page.keyboard.press('Escape')

  const dataTypeOptions = await openScopedMenu(
    page,
    dialog.locator('[data-cy="nsv-data-type"]')
  )
  await dataTypeOptions
    .filter({ hasText: /ct\s*term/i })
    .first()
    .click()
  await expect(dialog.locator('[data-cy="nsv-data-type"]')).toHaveClass(
    /v-select--selected/,
    { timeout: 10_000 }
  )

  await dialog.locator('[data-cy="nsv-code"] input').fill('MULTIAIC')
  await dialog.locator('[data-cy="nsv-label"] input').fill('Multi AIC label')
  await dialog.locator('[data-cy="nsv-name"] input').fill('multi_aic_label')
  const roleOptions = await openScopedMenu(
    page,
    dialog.locator('[data-cy="nsv-role"]')
  )
  await roleOptions.nth(0).click()
  await expect(dialog.locator('[data-cy="nsv-role"]')).toHaveClass(
    /v-select--selected/,
    { timeout: 10_000 }
  )

  await dialog.locator('[data-cy="nsv-length"] input').fill('10')

  await page.evaluate(() => {
    window.__demoLastWrite = null
  })
  await dialog.getByRole('button', { name: /save/i }).click()

  await expect
    .poll(() => page.evaluate(() => window.__demoLastWrite?.path))
    .toBe('/activity-item-classes')
  const lastWrite = await page.evaluate(() => window.__demoLastWrite)
  expect(lastWrite.body.activity_instance_classes).toHaveLength(2)

  spy.assertClean()
})
