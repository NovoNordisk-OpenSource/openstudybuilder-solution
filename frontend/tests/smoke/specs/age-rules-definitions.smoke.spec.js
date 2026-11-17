import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// The stored age rules carry no definition, so the tab looks it up in the
// codelist terms. Demo Study_000001 holds Age at Baseline Rule 1 and
// Age with 1 decimal digit (src/demo/fixtures).
const AGE_RULES_PATH = '/studies/Study_000001/study_properties/age_rules'
const RULE_1_DEFINITION = 'Age based on BirthDate and Baseline Visit Date'
const RULE_2_DEFINITION =
  'Age based on BirthDate and Date of Randomisation Visit'

test('smoke: Age Rules tab shows the rule definitions in the table, dropdown and info tooltip', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto(AGE_RULES_PATH)

  const table = page.locator('table').first()
  await expect(
    table.locator('thead th', { hasText: 'Definition' })
  ).toHaveCount(1, { timeout: 20_000 })
  await expect(
    table.locator('tbody tr', { hasText: 'Age at baseline rule' })
  ).toContainText(RULE_1_DEFINITION)

  await page.locator('[data-cy="edit-content"]').click()

  // Info button next to the field shows the selected rule's definition
  await page
    .locator('[data-cy="age_at_baseline_rule"] .v-input__append button')
    .hover()
  await expect(
    page.locator('.v-tooltip .v-overlay__content:visible', {
      hasText: RULE_1_DEFINITION,
    })
  ).toBeVisible()

  // Hovering an option shows that option's definition
  await page.locator('[data-cy="age_at_baseline_rule"] .v-field').click()
  const option = page.getByRole('option', { name: 'Age at Baseline Rule 2' })
  await option.hover()
  await expect(
    page.locator('.v-tooltip .v-overlay__content:visible', {
      hasText: RULE_2_DEFINITION,
    })
  ).toBeVisible()

  // The fields are rendered from a list, so check the selection still saves
  await page.evaluate(() => {
    window.__demoLastWrite = null
  })
  await option.click()
  await page.locator('[data-cy="save-button"]').click()
  await expect
    .poll(() => page.evaluate(() => window.__demoLastWrite?.path))
    .toBe('/studies/Study_000001')
  const body = await page.evaluate(() => window.__demoLastWrite.body)
  expect(
    body.current_metadata.high_level_study_design.age_at_baseline_rule_code
  ).toEqual({ term_uid: 'CTTerm_AGE_BL_2', name: 'Age at Baseline Rule 2' })

  spy.assertClean()
})
