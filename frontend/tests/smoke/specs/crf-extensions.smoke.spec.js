import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// CrfExtensionsManagementTable.vue's groupByNamespace() sorts the selected
// and available vendor attributes/elements by vendor_namespace.name and
// injects synthetic { isGroupHeader: true } rows between namespace runs
// (rendered as .namespace-group-header). These cases open the Vendor
// Extensions step for each CRF entity type in edit mode (stepper tabs are
// only free-navigable once isEdit() is true — see HorizontalStepperForm's
// `editable`/`save-from-any-step` props in CrfItemForm.vue and friends) and
// assert the grouping renders without crashing.

const CRF_ENTITY_CASES = [
  { label: 'CRF item', path: '/library/crf-builder/items' },
  { label: 'CRF item group', path: '/library/crf-builder/item-groups' },
  { label: 'CRF form', path: '/library/crf-builder/forms' },
]

for (const { label, path } of CRF_ENTITY_CASES) {
  test(`smoke: ${label} Vendor Extensions step groups attributes by namespace`, async ({
    page,
  }) => {
    await page.addInitScript(seedDemoAuth)
    const spy = setupConsoleSpy(page)

    await page.goto(path)

    // Open the first row's actions menu and edit it (isEdit() === true),
    // which is what unlocks free navigation between stepper tabs.
    const actionButton = page
      .locator('[data-cy="table-item-action-button"]')
      .first()
    await expect(actionButton).toBeVisible({ timeout: 15_000 })
    await actionButton.click()

    const editAction = page.locator('[data-cy="Edit"]').first()
    await expect(editAction).toBeVisible({ timeout: 5_000 })
    await editAction.click()

    const extensionsStep = page
      .locator('.v-stepper-item', { hasText: 'Vendor Extensions' })
      .first()
    await expect(extensionsStep).toBeVisible({ timeout: 15_000 })
    await extensionsStep.click()

    // Both sub-tables render, each with their own grouped rows.
    await expect(page.getByText('Existing Attributes')).toBeVisible({
      timeout: 10_000,
    })
    await expect(page.getByText('Available Attributes')).toBeVisible({
      timeout: 10_000,
    })

    // At least one namespace group header rendered in either table — proves
    // groupByNamespace() ran and the demo data has a vendor_namespace to
    // group by, rather than everything silently landing in one flat list.
    const groupHeaders = page.locator('.namespace-group-header')
    await expect(groupHeaders.first()).toBeVisible({ timeout: 10_000 })
    expect(await groupHeaders.count()).toBeGreaterThan(0)

    spy.assertClean()
  })
}
