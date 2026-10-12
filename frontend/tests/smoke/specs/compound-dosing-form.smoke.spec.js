import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Step-3 coverage for the Add Study Compound Dosing form. The shared FORM_CASES
// loop in forms.smoke.spec.js only opens step 1 and cancels, so nothing there
// reaches the dose value / dose frequency fields — which is where all of this
// form's logic lives:
//   - two Library/Free text radio groups, each swapping its field
//   - a Dose frequency dropdown grouped into the medicinal product's own
//     frequencies and the rest of the frequency codelist, via Vuetify subheader
//     pseudo-items
//
// No save is attempted, so this adds zero state mutation.
//
// Neither test cancels out at the end, deliberately: cancelling this form after
// a study element has been selected trips a pre-existing TypeError ("Cannot set
// properties of null (setting 'order')") from the disabled
// `v-model="form.study_element.order"` field writing back while close() resets
// `form` to {}. That predates the grouped dropdown, and asserting a clean
// console through it would fail for reasons unrelated to what these tests cover.

const DOSINGS_PATH =
  '/studies/Study_000001/study_interventions/study_compound_dosings'

// Sentence case, matching the committed locale strings
const MEDICINAL_PRODUCT_GROUP = 'Medicinal product frequencies'
const OTHER_GROUP = 'Other frequencies'

/** Open a Vuetify autocomplete/select and pick its first real option.
 *
 * Vuetify keeps the previous overlay in the DOM while it transitions out, so the
 * active menu is the visible one, not the first `.v-overlay__content` element.
 */
async function selectFirstOption(page, dataCy) {
  const field = page.locator(`[data-cy="${dataCy}"] .v-field__input`).first()
  await field.click()

  const overlay = page.locator('.v-overlay__content:visible').last()
  const option = overlay.locator('.v-list-item').first()

  await expect(option).toBeVisible({ timeout: 10_000 })
  await option.click()
}

/** Walk the stepper to step 3 (compound dosing information). */
async function openStepThree(page) {
  await page.goto(DOSINGS_PATH)
  await page.locator('[data-cy="add-study-compound-dosing"]').first().click()

  await expect(
    page.locator('[data-cy="form-body"]:visible').first()
  ).toBeVisible({ timeout: 15_000 })

  await selectFirstOption(page, 'study-element')
  await page.locator('[data-cy="continue-button"]:visible').first().click()

  await selectFirstOption(page, 'select-compound')
  await page.locator('[data-cy="continue-button"]:visible').first().click()

  // Step 3 is identified by its radio groups, which exist nowhere else
  await expect(page.locator('[data-cy="dose-frequency-source"]')).toBeVisible({
    timeout: 10_000,
  })
}

test('smoke: Compound dosing step 3 groups dose frequencies by source', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await openStepThree(page)

  // Library is the default for both sources, so the dropdown is the field shown
  await expect(page.locator('[data-cy="dose-frequency"]')).toBeVisible()
  await expect(
    page.locator('[data-cy="free-text-dose-frequency"]')
  ).toHaveCount(0)

  await page.locator('[data-cy="dose-frequency"] .v-field__input').click()

  const overlay = page.locator('.v-overlay__content:visible').last()
  await expect(overlay.locator('.v-list-item').first()).toBeVisible({
    timeout: 10_000,
  })

  // Two groups, the medicinal product's own frequencies first. Catches both a
  // dropped group and a subheader rendering as "[object Object]", which is what
  // happens if the pseudo-items stop carrying the key `item-title` resolves.
  const subheaders = overlay.locator('.v-list-subheader')
  await expect(subheaders).toHaveCount(2)
  await expect(subheaders.nth(0)).toHaveText(MEDICINAL_PRODUCT_GROUP)
  await expect(subheaders.nth(1)).toHaveText(OTHER_GROUP)

  // Subheaders are labels, not options — they must not be selectable
  await expect(
    overlay.locator('.v-list-item', { hasText: OTHER_GROUP })
  ).toHaveCount(0)

  await page.keyboard.press('Escape')

  spy.assertClean()
})

test('smoke: Compound dosing step 3 swaps each field on its source toggle', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await openStepThree(page)

  // Dose frequency: library dropdown -> free text field, and back
  await page.locator('[data-cy="dose-frequency-free-text"]').click()
  await expect(
    page.locator('[data-cy="free-text-dose-frequency"]')
  ).toBeVisible()
  await expect(page.locator('[data-cy="dose-frequency"]')).toHaveCount(0)

  await page.locator('[data-cy="dose-frequency-from-library"]').click()
  await expect(page.locator('[data-cy="dose-frequency"]')).toBeVisible()
  await expect(
    page.locator('[data-cy="free-text-dose-frequency"]')
  ).toHaveCount(0)

  // Dose value behaves the same way, and the two toggles are independent:
  // switching the dose value to free text must leave the frequency dropdown up
  await page.locator('[data-cy="dose-value-free-text"]').click()
  await expect(page.locator('[data-cy="free-text-dose-value"]')).toBeVisible()
  await expect(page.locator('[data-cy="dose-value"]')).toHaveCount(0)
  await expect(page.locator('[data-cy="dose-frequency"]')).toBeVisible()

  spy.assertClean()
})
