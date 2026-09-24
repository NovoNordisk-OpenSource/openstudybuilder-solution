import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Happy-path navigation flows. These walk the same paths a user would: pick a
// study from the list, drill from a table row into a detail page, etc. They
// catch regressions that pure URL-bar tests miss — broken click handlers,
// router-link generators that build the wrong URL, store updates that don't
// happen, etc.

test('smoke: select study from list lands on a study-required page', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto('/studies/select_or_add_study')

  // Wait for the studies table to render at least one row.
  const firstSelectButton = page.locator('button[title="Select study"]').first()
  await expect(firstSelectButton).toBeVisible({ timeout: 15_000 })
  await firstSelectButton.click()

  // The selected-study chip in the top bar updates and the active study UID
  // is stored. We don't navigate automatically — assert the chip flips from
  // "SELECT STUDY" to a study identifier (P-001-...).
  await expect(page.getByRole('button', { name: /^P-\d+/ })).toBeVisible({
    timeout: 5_000,
  })

  // Now navigate to a study-required route and confirm it renders without
  // bouncing to the study picker.
  await page.goto('/studies/Study_000001/study_status')
  await expect(
    page.locator('.page-title, .text-headline-large').first()
  ).toBeVisible({ timeout: 15_000 })

  spy.assertClean()
})

test('smoke: drill from activities table to activity overview', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto('/library/activities/activities')

  // First activity row's link goes to /library/activities/activities/{uid}/overview.
  const firstActivityLink = page
    .locator('a[href*="/library/activities/activities/"][href*="/overview"]')
    .first()
  await expect(firstActivityLink).toBeVisible({ timeout: 15_000 })
  await firstActivityLink.click()

  await expect(page).toHaveURL(
    /\/library\/activities\/activities\/.+\/overview/,
    {
      timeout: 10_000,
    }
  )
  await expect(
    page.locator('.page-title, .text-headline-large').first()
  ).toBeVisible({ timeout: 15_000 })

  spy.assertClean()
})

test('smoke: drill from sponsor codelists table via row actions menu', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  await page.goto('/library/sponsor')

  // The CodelistTable doesn't expose row-level links — it uses the shared
  // ActionsMenu (data-cy="table-item-action-button" → menu item with
  // data-cy="Show terms"). Open the first row's menu and route via
  // router.push (see SponsorTable.vue's openCodelistTerms handler).
  const firstActionButton = page
    .locator('[data-cy="table-item-action-button"]')
    .first()
  await expect(firstActionButton).toBeVisible({ timeout: 15_000 })
  await firstActionButton.click()

  const showTerms = page.locator('[data-cy="Show terms"]').first()
  await expect(showTerms).toBeVisible({ timeout: 5_000 })
  await showTerms.click()

  await expect(page).toHaveURL(/\/library\/.+\/terms\/?$/, { timeout: 10_000 })
  await expect(
    page.locator('.page-title, .text-headline-large').first()
  ).toBeVisible({ timeout: 15_000 })

  // The terms table itself should populate from /ct/codelists/terms. If the
  // demo paginated wrapper for that endpoint regresses, the page title still
  // renders but the table sits empty — assert on rows here so we catch it.
  const termRows = page.locator(
    '.v-data-table tbody tr:not(.v-data-table-rows-no-data):not(.v-data-table-rows-loading)'
  )
  await expect(termRows.first()).toBeVisible({ timeout: 15_000 })
  expect(await termRows.count()).toBeGreaterThan(0)

  spy.assertClean()
})

test('smoke: sidebar navigates to a dynamically-fetched CT library page', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)

  // SideBar.vue calls appStore.fetchCtLibraries() on mount, which GETs
  // /libraries and splices one menu entry per editable, non-excluded library
  // into the Code Lists tile (stores/app.js). Land on a Code Lists page so
  // that tile is expanded, then wait for the dynamic entry rather than
  // asserting on a specific library name — this exercises the store action
  // and the useEditableLibraries() composable's shared fetch without coupling
  // the test to which library the demo backend happens to synthesize.
  await page.goto('/library/sponsor')

  const dynamicLibraryLink = page
    .locator('.v-navigation-drawer a[href*="/library/ct/"]')
    .first()
  await expect(dynamicLibraryLink).toBeVisible({ timeout: 15_000 })
  const linkLabel = (await dynamicLibraryLink.innerText()).trim()

  await dynamicLibraryLink.click()

  // The route is 'ct/:library_name/:tab?' and CtLibraryTable's NavigationTabs
  // syncs the active catalogue tab into the URL (landing on .../<library>/All),
  // so allow that optional trailing segment rather than asserting on it.
  await expect(page).toHaveURL(/\/library\/ct\/[^/]+(\/[^/]+)?\/?$/, {
    timeout: 10_000,
  })

  // CtLibraryPage.vue renders "CT {library_name}" and overrides the level-2
  // breadcrumb with the same label used in the sidebar.
  await expect(page.locator('.page-title')).toContainText(linkLabel, {
    timeout: 15_000,
  })
  await expect(page.locator('.v-breadcrumbs')).toBeVisible({ timeout: 10_000 })
  const crumbs = await page.locator('.v-breadcrumbs-item').allInnerTexts()
  expect(crumbs.slice(0, 3)).toEqual(['Library', 'Code Lists', linkLabel])

  // CtLibraryTable.vue renders an "All" tab plus one per CT catalogue.
  await expect(page.getByRole('tab', { name: 'All' })).toBeVisible({
    timeout: 10_000,
  })

  spy.assertClean()
})
