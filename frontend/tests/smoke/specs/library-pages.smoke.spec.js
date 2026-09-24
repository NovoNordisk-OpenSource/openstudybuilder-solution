import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

const LIBRARY_PAGES = [
  ['Process overview', '/library/process_overview'],
  ['CDISC', '/library/cdisc'],
  ['CT catalogues', '/library/ct_catalogues'],
  ['CT packages', '/library/ct_packages'],
  ['Terms', '/library/terms'],
  ['Sponsor CT packages', '/library/sponsor-ct-packages'],
  // Dynamic CT library page — see the matching case in
  // breadcrumbs.smoke.spec.js for why "Library A" is a stable demo value.
  ['CT library (dynamic)', '/library/ct/Library%20A'],
  ['Snomed', '/library/snomed'],
  ['MedDRA', '/library/meddra'],
  ['MED-RT', '/library/medrt'],
  ['UNII', '/library/unii'],
  ['LOINC', '/library/loinc'],
  ['UCUM', '/library/ucum'],
  ['Activities', '/library/activities'],
  ['Units', '/library/units'],
  ['CRF builder', '/library/crf-builder'],
  ['Compounds', '/library/interventions/compounds'],
  ['Objective templates', '/library/objective_templates'],
  ['Endpoint templates', '/library/endpoint_templates'],
  ['Timeframe templates', '/library/timeframe_templates'],
  ['Activity instruction templates', '/library/activity_instruction_templates'],
  ['Criteria templates', '/library/criteria_templates'],
  ['Footnote templates', '/library/footnote_templates'],
  ['Project templates', '/library/project_templates'],
  ['Shared templates', '/library/shared_templates'],
  ['Supporting templates', '/library/supporting_templates'],
  ['CDASH', '/library/cdash'],
  ['SDTM', '/library/sdtm'],
  ['ADaM', '/library/adam'],
  ['Sponsor SDTM', '/library/sponsor-sdtm'],
  ['CDASH standards', '/library/cdash_standards'],
  ['SDTM standards (DMW)', '/library/sdtm_standards_dmw'],
  ['ADaM standards (CST)', '/library/adam_standards_cst'],
  ['ADaM standards (new)', '/library/adam_standards_new'],
  ['SDTM standards (CST)', '/library/sdtm_standards_cst'],
  ['Objective instances', '/library/objectives'],
  ['Endpoint instances', '/library/endpoints'],
  ['Timeframe instances', '/library/timeframe_instances'],
  ['Activity instruction instances', '/library/activity_instruction_instances'],
  ['Criteria instances', '/library/criteria_instances'],
  ['Footnote instances', '/library/footnote_instances'],
  ['Clinical programmes', '/library/clinical_programmes'],
  ['Projects', '/library/projects'],
  ['Data suppliers (library)', '/library/data-suppliers'],
  ['Template study', '/library/template_study'],
]

for (const [label, path] of LIBRARY_PAGES) {
  test(`smoke: ${label} renders without crashes`, async ({ page }) => {
    await page.addInitScript(seedDemoAuth)

    const spy = setupConsoleSpy(page)

    await page.goto(path)

    await expect(
      page.locator('.page-title, .text-headline-large').first()
    ).toBeVisible({ timeout: 15_000 })

    spy.assertClean()
  })
}
