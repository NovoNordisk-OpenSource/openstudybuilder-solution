import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

const SEED_STUDY_UID = 'Study_000001'

const STUDY_PAGES = [
  ['Study title', 'study_title'],
  ['Study purpose', 'study_purpose'],
  ['Study structure', 'study_structure'],
  ['Study population', 'population'],
  ['Study properties', 'study_properties'],
  ['Registry identifiers', 'registry_identifiers'],
  ['Study activities', 'activities'],
  ['Selection criteria', 'selection_criteria'],
  ['Study interventions', 'study_interventions'],
  ['Data specifications', 'data_specifications'],
  ['Protocol elements', 'protocol_elements'],
  ['Study disclosure', 'study_disclosure'],
  ['Data standard versions', 'data_standard_versions'],
  ['SDTM study design datasets', 'sdtm_study_design_datasets'],
  ['USDM listing', 'usdm'],
  ['ICH M11 listing', 'ichm11'],
  ['Analysis study metadata', 'analysis_study_metadata_new'],
]

for (const [label, segment] of STUDY_PAGES) {
  test(`smoke: ${label} renders without crashes`, async ({ page }) => {
    await page.addInitScript(seedDemoAuth)

    const spy = setupConsoleSpy(page)

    await page.goto(`/studies/${SEED_STUDY_UID}/${segment}`)

    await expect(
      page.locator('.page-title, .text-headline-large').first()
    ).toBeVisible({ timeout: 15_000 })

    spy.assertClean()
  })
}
