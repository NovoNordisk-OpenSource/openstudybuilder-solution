import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// CRF Compare loads a form at two versions (form -> item groups -> items, each
// at the version its parent pins) and lays the two trees out side by side.
// The demo fixtures in src/demo/fixtures/crfs.js hold "Vital Signs" 1.0 vs 2.0:
// a changed prompt, a term dropped and an item added.

async function pick(page, dataCy, optionText) {
  await page.locator(`[data-cy="${dataCy}"]`).click()
  await page.getByRole('option', { name: optionText }).first().click()
}

async function selectVitalSigns(page, side, version) {
  await pick(page, `crf-compare-${side}-library`, 'Library A')
  await page.locator(`[data-cy="crf-compare-${side}-form"] input`).click()
  await page.getByRole('option', { name: 'Vital Signs' }).click()
  await pick(page, `crf-compare-${side}-version`, version)
}

test('smoke: CRF Compare lists the differences between two form versions', async ({
  page,
}) => {
  test.setTimeout(60_000)
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto('/library/crf-builder/crf-compare')

  const run = page.locator('[data-cy="crf-compare-run"]')
  await expect(run).toBeDisabled({ timeout: 15_000 })

  await selectVitalSigns(page, 'left', '1.0')
  await selectVitalSigns(page, 'right', '2.0')
  await expect(run).toBeEnabled()
  await run.click()

  const banner = page.locator('[data-cy="crf-compare-banner"]')
  await expect(banner).toContainText('Date of examination')
  await expect(banner).toContainText('Position')
  await expect(banner).toContainText('Anatomical Location')

  const toggle = page.locator('[data-cy="crf-compare-banner-toggle"]')
  await toggle.click()
  await expect(banner.locator('ul')).toBeHidden()
  await toggle.click()
  await expect(banner.locator('ul')).toBeVisible()

  const rows = page.locator('[data-cy="crf-compare-row"]')
  const allRows = await rows.count()
  await page.locator('[data-cy="crf-compare-only-differences"] input').check()
  expect(await rows.count()).toBeLessThan(allRows)

  expect(spy.errors).toEqual([])
})

test('smoke: CRF Compare arrows apply a difference onto the other form', async ({
  page,
}) => {
  test.setTimeout(60_000)
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto('/library/crf-builder/crf-compare')
  await expect(page.locator('[data-cy="crf-compare-run"]')).toBeDisabled({
    timeout: 15_000,
  })
  await selectVitalSigns(page, 'left', '1.0')
  await selectVitalSigns(page, 'right', '2.0')
  await page.locator('[data-cy="crf-compare-run"]').click()

  await page
    .locator('[data-cy="crf-compare-row"]', { hasText: 'Date of examination' })
    .first()
    .click()

  // The left form shows an older item version, so only copying onto the right
  // form (which shows the latest) is allowed to start.
  await page.locator('[data-cy="crf-compare-apply-right"]').click()
  const dialog = page.locator('.v-dialog')
  await expect(dialog).toContainText('Date of examination')
  await expect(dialog).toContainText('• Prompt')
  await dialog.locator('[data-cy="continue-popup"]').click()

  await expect
    .poll(() =>
      page.evaluate(
        () =>
          globalThis.__demoLastWrite?.method +
          ' ' +
          globalThis.__demoLastWrite?.path
      )
    )
    .toContain('PATCH /odms/items/CrfItem_000002')
  const body = await page.evaluate(() => globalThis.__demoLastWrite.body)
  expect(body.prompt).toBe('DD-MM-YYYY')

  expect(spy.errors).toEqual([])
})

test('smoke: CRF Compare shows extra attributes once they are switched on', async ({
  page,
}) => {
  test.setTimeout(60_000)
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto('/library/crf-builder/crf-compare')
  await expect(page.locator('[data-cy="crf-compare-run"]')).toBeDisabled({
    timeout: 15_000,
  })
  await selectVitalSigns(page, 'left', '1.0')
  await selectVitalSigns(page, 'right', '2.0')
  await page.locator('[data-cy="crf-compare-run"]').click()

  const banner = page.locator('[data-cy="crf-compare-banner"]')
  await expect(banner).not.toContainText('(CRF form)')
  await expect(
    page.locator('[data-cy="crf-compare-left-form-row"]')
  ).toHaveCount(0)

  await page.locator('[data-cy="crf-compare-attributes"]').click()
  await page.locator('[data-cy="crf-compare-attribute-form.oid"] input').check()

  await expect(
    page.locator('[data-cy="crf-compare-left-form-row"]')
  ).toContainText('F.VS')
  await expect(banner).toContainText('(CRF form)')

  expect(spy.errors).toEqual([])
})

test('smoke: CRF Compare accepts an ODM XML file as a side', async ({
  page,
}) => {
  test.setTimeout(60_000)
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto('/library/crf-builder/crf-compare')
  const run = page.locator('[data-cy="crf-compare-run"]')
  await expect(run).toBeDisabled({ timeout: 15_000 })

  await page.locator('[data-cy="crf-compare-left-use-file"] input').check()
  await page
    .locator('[data-cy="crf-compare-left-xml-file"] input')
    .setInputFiles({
      name: 'vs.xml',
      mimeType: 'text/xml',
      buffer: Buffer.from('<ODM/>'),
    })
  await expect(
    page.locator('[data-cy="crf-compare-left-file-hint"]')
  ).toBeVisible()
  await selectVitalSigns(page, 'right', '2.0')
  await expect(run).toBeEnabled()
  await run.click()
  await expect(page.locator('[data-cy="crf-compare-banner"]')).toBeVisible()

  expect(spy.errors).toEqual([])
})
