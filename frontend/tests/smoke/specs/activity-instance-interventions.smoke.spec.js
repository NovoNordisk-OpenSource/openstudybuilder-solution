import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Regression guard for the "enable interventions on front-end" change: the
// activity_instance_wizard_stepper_interventions flag adds an 'Interventions'
// activity instance class option to the "Add activity instance" wizard, and
// the step-3 tab title switches to match it once selected.
test('smoke: Add activity instance wizard offers Interventions and retitles step 3', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)

  const spy = setupConsoleSpy(page)

  await page.goto('/library/activities/activity-instances')

  const addButton = page.locator('[data-cy="add-activity"]').first()
  await expect(addButton).toBeVisible({ timeout: 15_000 })
  await addButton.click()

  const dialog = page.locator('[data-cy="form-body"]:visible')
  await expect(dialog).toBeVisible({ timeout: 10_000 })

  const firstRowCheckbox = dialog
    .locator('tbody tr')
    .first()
    .locator('input[type="checkbox"]')
  await expect(firstRowCheckbox).toBeVisible({ timeout: 20_000 })
  await firstRowCheckbox.check()

  await dialog.locator('[data-cy="continue-button"]').click()

  const classSelect = dialog.getByLabel('Activity instance class')
  await expect(classSelect).toBeVisible({ timeout: 10_000 })

  const interventionsOption = page.getByRole('option', {
    name: 'Interventions',
  })
  await expect(async () => {
    await classSelect.click({ force: true })
    await expect(interventionsOption).toBeVisible({ timeout: 1_000 })
  }).toPass({ timeout: 15_000 })
  await interventionsOption.click()

  await expect(
    dialog.locator('.v-stepper-item', { hasText: 'Interventions' })
  ).toBeVisible()

  spy.assertClean()
})
