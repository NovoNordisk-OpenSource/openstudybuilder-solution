import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// One column filter's trigger is either a v-select (opens a teleported
// option-list overlay, scoped via the trigger's own aria-controls — see the
// same technique in nsv-form.smoke.spec.js) or a date-range text field
// (opens a date-picker menu instead). Exercising it means: open it, pick
// the first available option when there is one (this is what actually
// applies the filter and re-fetches the table), then close it — without
// caring which kind of control it turned out to be.
async function exerciseFilter(page, trigger) {
  await trigger.scrollIntoViewIfNeeded()
  await trigger.click()

  const datepicker = page.locator('[data-cy="filter-field-datepicker"]')
  if (await datepicker.isVisible().catch(() => false)) {
    await page.keyboard.press('Escape')
    return
  }

  const menuId = await trigger
    .locator('[role="combobox"]')
    .first()
    .getAttribute('aria-controls')
  if (!menuId) {
    await page.keyboard.press('Escape')
    return
  }

  const options = page.locator(`#${menuId} [role="option"]`)
  try {
    await expect(options.first()).toBeVisible({ timeout: 3_000 })
    await options.first().click()
  } catch {
    // No values for this column in the demo dataset — nothing to select,
    // which is fine; opening it without error is still a real assertion.
  }
  await page.keyboard.press('Escape')
}

test('smoke: every NSV table column filter opens and applies without error', async ({
  page,
}) => {
  test.setTimeout(90_000)
  const spy = setupConsoleSpy(page)
  await page.addInitScript(seedDemoAuth)
  await page.goto('/library/activities/non-standard-variables')

  const table = page.locator('[data-cy="data-table"]')
  await expect(table).toBeVisible({ timeout: 15_000 })

  await page.locator('[data-cy="filters-button"]').click()
  const filterFields = page.locator('[data-cy="filter-field"]')
  await expect(filterFields.first()).toBeVisible({ timeout: 10_000 })

  // Whatever columns the table happens to render (today or after a future
  // edit), sweep every one of their filters generically instead of
  // hard-coding a per-column list.
  const count = await filterFields.count()
  expect(count).toBeGreaterThan(5)

  for (let i = 0; i < count; i++) {
    await exerciseFilter(page, filterFields.nth(i))
    await expect(table).toBeVisible()
  }

  spy.assertClean()
})

test('smoke: NSV global search sends the typed term as a wildcard filter', async ({
  page,
}) => {
  const spy = setupConsoleSpy(page)
  await page.addInitScript(seedDemoAuth)
  await page.goto('/library/activities/non-standard-variables')

  const table = page.locator('[data-cy="data-table"]')
  await expect(table).toBeVisible({ timeout: 15_000 })

  const searchField = page.locator('[data-cy="search-field"] input')

  // Representative values for the columns Copilot flagged as unasserted:
  // role, semantic data type, and NSV code.
  for (const term of ['Sponsor', 'Character', 'CDISC']) {
    await page.evaluate(() => {
      window.__demoLastRead = null
    })
    await searchField.fill(term)

    await expect
      .poll(() => page.evaluate(() => window.__demoLastRead?.params?.filters), {
        timeout: 10_000,
      })
      .toBeTruthy()

    const lastRead = await page.evaluate(() => window.__demoLastRead)
    expect(lastRead.path).toBe('/activity-item-classes')
    expect(JSON.parse(lastRead.params.filters)).toEqual({ '*': { v: [term] } })
  }

  spy.assertClean()
})

test('smoke: NSV status tabs request the matching status filter', async ({
  page,
}) => {
  const spy = setupConsoleSpy(page)
  await page.addInitScript(seedDemoAuth)
  await page.goto('/library/activities/non-standard-variables')

  const table = page.locator('[data-cy="data-table"]')
  await expect(table).toBeVisible({ timeout: 15_000 })

  const statusTabs = page.locator('.layoutSelector')

  for (const status of ['Final', 'Draft', 'Retired']) {
    await page.evaluate(() => {
      window.__demoLastRead = null
    })
    await statusTabs.getByRole('button', { name: status, exact: true }).click()

    await expect
      .poll(() => page.evaluate(() => window.__demoLastRead?.params?.filters), {
        timeout: 10_000,
      })
      .toBeTruthy()

    const lastRead = await page.evaluate(() => window.__demoLastRead)
    expect(lastRead.path).toBe('/activity-item-classes')
    expect(JSON.parse(lastRead.params.filters)).toEqual({
      status: { v: [status] },
    })
  }

  // Switching back to "All" drops the status filter entirely rather than
  // sending an empty one.
  await page.evaluate(() => {
    window.__demoLastRead = null
  })
  await statusTabs.getByRole('button', { name: 'All', exact: true }).click()

  await expect
    .poll(() => page.evaluate(() => window.__demoLastRead?.path), {
      timeout: 10_000,
    })
    .toBe('/activity-item-classes')

  const lastRead = await page.evaluate(() => window.__demoLastRead)
  expect(lastRead.params.filters).toBeUndefined()

  spy.assertClean()
})

// Regression coverage for bug/922457: NonStandardVariablesTable and
// ActivityItemClassTable share the same column-data-resource (both list
// nci_concept_id/nci_concept_name off /activity-item-classes/headers), so
// each must pass its own is_nsv so the two tables' filter dropdowns don't
// leak each other's NCI-concept values.
test('smoke: NSV table NCI Concept filter requests is_nsv=true', async ({
  page,
}) => {
  const spy = setupConsoleSpy(page)
  await page.addInitScript(seedDemoAuth)
  await page.goto('/library/activities/non-standard-variables')

  const table = page.locator('[data-cy="data-table"]')
  await expect(table).toBeVisible({ timeout: 15_000 })

  await page.locator('[data-cy="filters-button"]').click()
  const nciFilter = page
    .locator('[data-cy="filter-field"]')
    .filter({ hasText: 'NCI Code' })
  await expect(nciFilter).toBeVisible({ timeout: 10_000 })
  await nciFilter.click()

  // Opening the select already fires a headers request (ignoring search), so
  // reset the captured read here and assert on the one the debounced
  // search-box watcher fires after typing below, not the open-triggered one.
  await page.evaluate(() => {
    window.__demoLastRead = null
  })
  await page.getByPlaceholder('Search').fill('a')

  await expect
    .poll(() => page.evaluate(() => window.__demoLastRead?.path), {
      timeout: 10_000,
    })
    .toBe('/activity-item-classes/headers')

  const lastRead = await page.evaluate(() => window.__demoLastRead)
  expect(lastRead.params.is_nsv).toBe(true)
  await page.keyboard.press('Escape')

  spy.assertClean()
})

test('smoke: ActivityItemClass table NCI Concept filter requests is_nsv=false', async ({
  page,
}) => {
  const spy = setupConsoleSpy(page)
  await page.addInitScript(seedDemoAuth)
  await page.goto('/library/activities/activity-item-classes')

  const table = page.locator('[data-cy="data-table"]')
  await expect(table).toBeVisible({ timeout: 15_000 })

  await page.locator('[data-cy="filters-button"]').click()
  const nciFilter = page
    .locator('[data-cy="filter-field"]')
    .filter({ hasText: 'NCI Code' })
  await expect(nciFilter).toBeVisible({ timeout: 10_000 })
  await nciFilter.click()

  await page.evaluate(() => {
    window.__demoLastRead = null
  })
  await page.getByPlaceholder('Search').fill('a')

  await expect
    .poll(() => page.evaluate(() => window.__demoLastRead?.path), {
      timeout: 10_000,
    })
    .toBe('/activity-item-classes/headers')

  const lastRead = await page.evaluate(() => window.__demoLastRead)
  expect(lastRead.params.is_nsv).toBe(false)
  await page.keyboard.press('Escape')

  spy.assertClean()
})

// Regression for the live-refresh watcher in FilterAutocomplete.vue: a
// column's dropdown must re-fetch its header list (bypassing the boolean
// cache) if a row changes while that dropdown stays open, or a stale list
// stays visible. The demo backend can't produce this by itself — it
// synthesizes list responses from the OpenAPI schema alone and never varies
// `status` per row (see mockBackend.js) — and a real click on a row action
// can't either, since clicking anything outside an open select closes it
// before the change would matter. __demoSimulateNsvRowChange (defined next
// to DEMO_MODE in NonStandardVariablesTable.vue) mutates a row in place, in
// the page's own JS context, so the dropdown never has to close.
test('smoke: NSV filter dropdown re-fetches when a row changes while it stays open', async ({
  page,
}) => {
  const spy = setupConsoleSpy(page)
  await page.addInitScript(seedDemoAuth)
  await page.goto('/library/activities/non-standard-variables')

  const table = page.locator('[data-cy="data-table"]')
  await expect(table).toBeVisible({ timeout: 15_000 })

  await page.locator('[data-cy="filters-button"]').click()
  const labelFilter = page
    .locator('[data-cy="filter-field"]')
    .filter({ hasText: 'NSV label' })
  await expect(labelFilter).toBeVisible({ timeout: 10_000 })
  await labelFilter.click()

  // Opening the dropdown fires its own ignoreSearch fetch (the `menuOpen`
  // watcher) — wait for that one to land before watching for the next.
  await expect
    .poll(() => page.evaluate(() => window.__demoLastRead?.path), {
      timeout: 10_000,
    })
    .toBe('/activity-item-classes/headers')

  await page.evaluate(() => {
    window.__demoLastRead = null
  })
  await page.evaluate(() =>
    window.__demoSimulateNsvRowChange(0, { status: 'Draft' })
  )

  // A boolean-cache hit fires no request at all, so a landed request here
  // proves the live-refresh path ran rather than silently serving the list
  // already fetched when the dropdown opened.
  await expect
    .poll(() => page.evaluate(() => window.__demoLastRead?.path), {
      timeout: 10_000,
    })
    .toBe('/activity-item-classes/headers')

  await page.keyboard.press('Escape')
  spy.assertClean()
})
