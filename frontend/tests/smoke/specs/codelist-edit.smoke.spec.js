import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Both the codelist and term detail pages gate the "edit sponsor values"
// pencil on `possible_actions.includes('edit')`. The schema walker emits a
// real action set in demo mode so the pencil renders. These two tests open
// each form, confirm it mounts, and cancel cleanly — catching regressions in
// CodelistSponsorValuesForm.vue / CodelistTermSponsorValuesForm.vue mounting
// and in the upstream possible_actions plumbing.

test('smoke: edit sponsor values form opens from codelist detail and cancels cleanly', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto('/library/sponsor')

  // Drill via the action menu's Edit entry — same path the user takes.
  const firstActionButton = page
    .locator('[data-cy="table-item-action-button"]')
    .first()
  await expect(firstActionButton).toBeVisible({ timeout: 15_000 })
  await firstActionButton.click()
  await page.locator('[data-cy="Edit"]').first().click()

  // Edit pencil only appears once codelistNames is hydrated and its
  // possible_actions array contains 'edit'.
  const editPencil = page.locator('[data-cy="edit-sponsor-values"]').first()
  await expect(editPencil).toBeVisible({ timeout: 15_000 })
  await editPencil.click()

  // Form mounts inside a v-dialog as a v-card with data-cy="form-body".
  const formBody = page.locator('[data-cy="form-body"]:visible').first()
  await expect(formBody).toBeVisible({ timeout: 5_000 })

  // CodelistSponsorValuesForm uses a plain text Cancel button (no data-cy).
  await formBody.getByRole('button', { name: 'Cancel' }).first().click()

  await expect(page.locator('[data-cy="form-body"]:visible')).toHaveCount(0, {
    timeout: 5_000,
  })

  spy.assertClean()
})

test('smoke: edit sponsor values form opens from term detail and cancels cleanly', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  // Drill: sponsor codelists → Show terms → first term → View or edit details.
  await page.goto('/library/sponsor')
  await page
    .locator('[data-cy="table-item-action-button"]')
    .first()
    .click({ timeout: 15_000 })
  await page.locator('[data-cy="Show terms"]').first().click()

  const termActionButton = page
    .locator('.v-main .v-data-table [data-cy="table-item-action-button"]')
    .first()
  await expect(termActionButton).toBeVisible({ timeout: 15_000 })
  await termActionButton.click()
  await page.locator('[data-cy="View or edit details"]').first().click()

  const editPencil = page.locator('[data-cy="edit-sponsor-values"]').first()
  await expect(editPencil).toBeVisible({ timeout: 15_000 })
  await editPencil.click()

  const formBody = page.locator('[data-cy="form-body"]:visible').first()
  await expect(formBody).toBeVisible({ timeout: 5_000 })

  await formBody.getByRole('button', { name: 'Cancel' }).first().click()

  await expect(page.locator('[data-cy="form-body"]:visible')).toHaveCount(0, {
    timeout: 5_000,
  })

  spy.assertClean()
})
