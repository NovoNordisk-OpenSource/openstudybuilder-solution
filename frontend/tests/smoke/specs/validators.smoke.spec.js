import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Validator coverage for the Add Activity form. Picks one form representative
// of the project's validator usage (formRules.required + formRules.sameAs via
// SentenceCaseNameField) and pounds it: empty submit, divergent sentence
// case, recovery. Catches regressions in:
//   - rule wiring (`:rules` array dropped from a field)
//   - submit gating (observer.validate() no longer blocks emit('submit'))
//   - i18n (error messages render as translated strings, not raw keys)
//
// The form is opened against the demo backend; no save is attempted, so this
// adds zero state mutation.
//
// Note on counting: SentenceCaseNameField wraps its input in its own <v-form>,
// so the parent observer's validate() doesn't recurse into it on the very
// first submit. Once any field has been written, the sub-form's rules join
// in. Assertions below are written to tolerate that handoff.

const REQUIRED_MESSAGE = 'This field is required'
const SAME_AS_MESSAGE =
  'Sentence case name can only differ in case compared to name value'

test('smoke: Add activity form blocks submit and surfaces validator errors', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto('/library/activities/activities')
  await page.locator('[data-cy="add-activity"]').first().click()

  const formBody = page.locator('[data-cy="form-body"]:visible').first()
  await expect(formBody).toBeVisible({ timeout: 15_000 })

  await expect(
    page.locator('[data-cy="sentence-case-name-field"]')
  ).toBeVisible({ timeout: 10_000 })

  const saveButton = page.locator('[data-cy="save-button"]:visible').first()
  const requiredErrors = page
    .locator('.v-messages__message:visible')
    .filter({ hasText: REQUIRED_MESSAGE })
  const sameAsErrors = page
    .locator('.v-messages__message:visible')
    .filter({ hasText: SAME_AS_MESSAGE })

  // 1. Empty submit — at least three required errors fire on the parent
  //    form (activity_group, activity_subgroup, name). Form does NOT close.
  await saveButton.click()
  await expect
    .poll(() => requiredErrors.count(), { timeout: 5_000 })
    .toBeGreaterThanOrEqual(3)
  await expect(formBody).toBeVisible()

  // 2. Real name — its required error clears; group + subgroup remain on
  //    the parent. The sub-form may also contribute its own required error
  //    once it engages, so allow up to 3 here.
  const nameField = page
    .locator('[data-cy="activityform-activity-name-field"] input')
    .first()
  await nameField.fill('Smoke Test Activity')
  await saveButton.click()
  await expect
    .poll(() => requiredErrors.count(), { timeout: 5_000 })
    .toBeGreaterThanOrEqual(2)
  await expect(formBody).toBeVisible()

  // SentenceCaseNameField auto-derives lowercase(name).
  const sentenceField = page
    .locator('[data-cy="sentence-case-name-field"] input')
    .first()
  await expect(sentenceField).toHaveValue('smoke test activity', {
    timeout: 2_000,
  })

  // 3. Divergent sentence-case value — sameAs rule fires.
  await sentenceField.fill('completely different')
  await sentenceField.blur()
  await expect(sameAsErrors).toHaveCount(1, { timeout: 5_000 })
  await expect(formBody).toBeVisible()

  // 4. Restore matching sentence case — sameAs clears.
  await sentenceField.fill('smoke test activity')
  await sentenceField.blur()
  await expect(sameAsErrors).toHaveCount(0, { timeout: 5_000 })

  // Cancel out — never submit. Discards the partial form state via the
  // continue-popup confirm if present.
  await page.locator('[data-cy="cancel-button"]:visible').first().click()
  const continueButton = page.locator('[data-cy="continue-popup"]:visible')
  try {
    await expect(continueButton.first()).toBeVisible({ timeout: 1_000 })
    await continueButton.first().click()
  } catch {
    // No confirm dialog.
  }
  await expect(page.locator('[data-cy="form-body"]:visible')).toHaveCount(0, {
    timeout: 5_000,
  })

  spy.assertClean()
})
