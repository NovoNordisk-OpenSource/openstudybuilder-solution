import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

const FORM_CASES = [
  {
    label: 'Add study',
    path: '/studies/select_or_add_study',
    addCy: 'add-study',
  },
  {
    label: 'Add activity',
    path: '/library/activities/activities',
    addCy: 'add-activity',
  },
  {
    label: 'Add unit',
    path: '/library/units',
    addCy: 'add-unit',
  },
  {
    label: 'Add clinical programme',
    path: '/library/clinical_programmes',
    addCy: 'add-clinical-programme',
  },
  {
    label: 'Add project',
    path: '/library/projects',
    addCy: 'add-project',
  },
  {
    label: 'Add data supplier',
    path: '/library/data-suppliers',
    addCy: 'add-data-supplier',
  },
  {
    label: 'Add objective template',
    path: '/library/objective_templates',
    addCy: 'add-template',
  },
  {
    label: 'Add endpoint template',
    path: '/library/endpoint_templates',
    addCy: 'add-template',
  },
  {
    label: 'Add timeframe template',
    path: '/library/timeframe_templates',
    addCy: 'add-template',
  },
  {
    label: 'Add criteria template',
    path: '/library/criteria_templates',
    addCy: 'add-template',
  },
  {
    label: 'Add footnote template',
    path: '/library/footnote_templates',
    addCy: 'add-template',
  },
  {
    label: 'Add activity instruction template',
    path: '/library/activity_instruction_templates',
    addCy: 'add-template',
  },
  {
    label: 'Add study activity',
    path: '/studies/Study_000001/activities/list',
    addCy: 'add-study-activity',
  },
  {
    label: 'Add study branch arm',
    path: '/studies/Study_000001/study_structure/branches',
    addCy: 'add-study-branch-arm',
  },
  {
    label: 'Add study cohort',
    path: '/studies/Study_000001/study_structure/cohorts',
    addCy: 'add-study-cohort',
  },
  {
    label: 'Add study objective',
    path: '/studies/Study_000001/study_purpose/objectives',
    addCy: 'add-study-objective',
  },
  {
    label: 'Add study visit',
    path: '/studies/Study_000001/study_structure/visits',
    addCy: 'add-visit',
  },
  {
    label: 'Add study compound',
    path: '/studies/Study_000001/study_interventions/study_compounds',
    addCy: 'add-study-compound',
  },
  {
    label: 'Add study compound dosing',
    path: '/studies/Study_000001/study_interventions/study_compound_dosings',
    addCy: 'add-study-compound-dosing',
  },
  {
    label: 'Add CRF collection',
    path: '/library/crf-builder/collections',
    addCy: 'add-crf-collection',
  },
  {
    label: 'Add CRF form',
    path: '/library/crf-builder/forms',
    addCy: 'add-crf-form',
  },
  {
    label: 'Add CRF item group',
    path: '/library/crf-builder/item-groups',
    addCy: 'add-crf-item-group',
  },
  {
    label: 'Add CRF item',
    path: '/library/crf-builder/items',
    addCy: 'add-crf-item',
  },
  {
    label: 'Add non-standard variable',
    path: '/library/activities/non-standard-variables',
    addCy: 'add-non-standard-variable',
  },
  {
    label: 'Add sponsor codelist',
    path: '/library/sponsor',
    addCy: 'add-sponsor-codelist',
  },
  {
    label: 'Add study criteria',
    path: '/studies/Study_000001/selection_criteria',
    addCy: 'add-study-criteria',
  },
  {
    label: 'Add CT standard version',
    path: '/studies/Study_000001/data_standard_versions',
    addCy: 'add-ct-standard-version',
  },
  // Deferred:
  //   add-term-button — gated by `codelistAttributes.extensible`; only visible
  //     inside a specific extensible codelist's term page, not at /library/terms.
  //   add-study-footnote — toggles SoA "footnote mode" (no modal); the actual
  //     footnote form is reached by then clicking an SoA target.
]

for (const { label, path, addCy } of FORM_CASES) {
  test(`smoke: ${label} form opens and cancels cleanly`, async ({ page }) => {
    await page.addInitScript(seedDemoAuth)

    const spy = setupConsoleSpy(page)

    await page.goto(path)

    const addButton = page.locator(`[data-cy="${addCy}"]`).first()
    await expect(addButton).toBeVisible({ timeout: 15_000 })
    await addButton.click()

    // Some tables wrap their form (which is itself a v-dialog) in another
    // v-dialog, so role="dialog" can match both the outer wrapper and the
    // inner form. Pick the dialog that actually has a cancel button.
    const visibleDialog = page
      .locator('[role="dialog"]:visible')
      .filter({ has: page.locator('[data-cy="cancel-button"]') })
      .first()
    await expect(visibleDialog).toBeVisible({ timeout: 10_000 })

    const cancelButton = visibleDialog
      .locator('[data-cy="cancel-button"]')
      .first()
    await expect(cancelButton).toBeVisible({ timeout: 5_000 })
    await cancelButton.click()

    // HorizontalStepperForm-based forms show a "discard changes?" confirm
    // dialog whenever formStore.isEmpty returns false. Confirm it if present.
    const continueButton = page.locator('[data-cy="continue-popup"]:visible')
    try {
      await expect(continueButton.first()).toBeVisible({ timeout: 1_000 })
      await continueButton.first().click()
    } catch {
      // No confirm dialog — SimpleFormDialog closed directly.
    }

    await expect(page.locator('[role="dialog"]:visible')).toHaveCount(0, {
      timeout: 5_000,
    })

    await expect(addButton).toBeVisible()

    spy.assertClean()
  })
}
