import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

// Breadcrumbs are meant to mirror the menu hierarchy — they should show what
// you clicked to get to where you are. The trails below are the expected
// click path per route. Most pages also append an in-page sub-tab to the
// trail (e.g. "All" on a list, "Title Page" on protocol elements); those are
// included verbatim because they are stable per route and removing them
// would weaken the assertion.

const STUDY_UID = 'Study_000001'

const DEEP_LINK_CASES = [
  // Library — landing pages
  { path: '/library/summary', trail: ['Library', 'About Library'] },
  {
    path: '/library/sponsor',
    trail: ['Library', 'Code Lists', 'Sponsor', 'All'],
  },
  {
    path: '/library/ct_catalogues',
    trail: ['Library', 'Code Lists', 'CT Catalogues', 'All'],
  },
  {
    path: '/library/ct_packages',
    trail: [
      'Library',
      'Code Lists',
      'CT Packages',
      'Catalogue A',
      'CT Package A',
    ],
  },
  {
    path: '/library/sponsor-ct-packages',
    trail: [
      'Library',
      'Code Lists',
      'Sponsor CT Packages',
      'Catalogue A',
      'CT Package A',
    ],
  },
  // Dynamic CT library page (router/index.js 'CtLibrary' route, populated by
  // useAppStore().fetchCtLibraries()). The demo backend's GET /libraries
  // returns a single, deterministically-named item (schema-driven: humanized
  // schema name "Library" + letter "A" for the only array entry), so
  // "Library A" is a stable value for this fixture, not a magic string.
  // CtLibraryPage.vue overrides the level-2 breadcrumb with the actual
  // route param since every CT library shares the 'CtLibrary' route name.
  {
    path: '/library/ct/Library%20A',
    trail: ['Library', 'Code Lists', 'Library A', 'All'],
  },
  { path: '/library/terms', trail: ['Library', 'Code Lists', 'Terms'] },
  { path: '/library/snomed', trail: ['Library', 'Dictionaries', 'SNOMED'] },
  { path: '/library/medrt', trail: ['Library', 'Dictionaries', 'MED-RT'] },
  { path: '/library/unii', trail: ['Library', 'Dictionaries', 'UNII'] },
  { path: '/library/ucum', trail: ['Library', 'Dictionaries', 'UCUM'] },

  // Library — concepts/activities tabs
  {
    path: '/library/activities/activities',
    trail: ['Library', 'Concepts', 'Activities', 'Activities'],
  },
  {
    path: '/library/activities/activity-instances',
    trail: ['Library', 'Concepts', 'Activities', 'Activity Instances'],
  },
  {
    path: '/library/activities/activity-groups',
    trail: ['Library', 'Concepts', 'Activities', 'Activity Groups'],
  },
  {
    path: '/library/activities/activity-instance-classes',
    trail: ['Library', 'Concepts', 'Activities', 'Activity Instance Classes'],
  },
  {
    path: '/library/activities/activity-item-classes',
    trail: ['Library', 'Concepts', 'Activities', 'Activity Item Classes'],
  },
  {
    path: '/library/activities/activity-subgroups',
    trail: ['Library', 'Concepts', 'Activities', 'Activity Subgroups'],
  },
  // /library/activities/requested-activities is intentionally omitted —
  // the demo build enables the streamline_placeholder_activities feature
  // flag, which hides the "Requested Activities" tab.
  { path: '/library/units', trail: ['Library', 'Concepts', 'Units'] },
  {
    path: '/library/crf-viewer',
    trail: ['Library', 'Data Collection Standards', 'CRF Viewer'],
  },

  // Library — syntax templates
  {
    path: '/library/objective_templates',
    trail: ['Library', 'Syntax Templates', 'Objectives', 'Parent'],
  },
  {
    path: '/library/endpoint_templates',
    trail: ['Library', 'Syntax Templates', 'Endpoints', 'Parent'],
  },
  {
    path: '/library/timeframe_templates',
    trail: ['Library', 'Syntax Templates', 'Time Frames', 'Parent'],
  },
  {
    path: '/library/criteria_templates',
    trail: [
      'Library',
      'Syntax Templates',
      'Criteria',
      'CT Codelist Term A',
      'Parent',
    ],
  },
  {
    path: '/library/footnote_templates',
    trail: [
      'Library',
      'Syntax Templates',
      'Footnotes',
      'CT Codelist Term A',
      'Parent',
    ],
  },

  // Library — template instantiations
  {
    path: '/library/objectives',
    trail: ['Library', 'Template Instantiations', 'Objectives'],
  },
  {
    path: '/library/endpoints',
    trail: ['Library', 'Template Instantiations', 'Endpoints'],
  },
  {
    path: '/library/timeframe_instances',
    trail: ['Library', 'Template Instantiations', 'Time Frames'],
  },
  {
    path: '/library/criteria_instances',
    trail: [
      'Library',
      'Template Instantiations',
      'Criteria',
      'CT Codelist Term A',
    ],
  },
  {
    path: '/library/footnote_instances',
    trail: [
      'Library',
      'Template Instantiations',
      'Footnotes',
      'CT Codelist Term A',
    ],
  },

  // Library — admin definitions
  {
    path: '/library/clinical_programmes',
    trail: ['Library', 'Admin Definitions', 'Clinical Programmes'],
  },
  {
    path: '/library/projects',
    trail: ['Library', 'Admin Definitions', 'Projects'],
  },

  // Library — overview pages (drill-in from row)
  {
    path: '/library/activities/activities/Activity_000001/overview',
    trail: ['Library', 'Concepts', 'Activities', 'Activities', 'Demo Activity'],
  },
  {
    path: '/library/activities/activity-instances/ActivityInstance_000001/overview',
    trail: [
      'Library',
      'Concepts',
      'Activities',
      'Activity Instances',
      'Simple Activity Instance A',
    ],
  },
  {
    path: '/library/activities/activity-groups/ActivityGroup_000001/overview',
    trail: [
      'Library',
      'Concepts',
      'Activities',
      'Activity Groups',
      'Demo Activity Group',
    ],
  },
  {
    path: '/library/activities/activity-instance-classes/ActivityInstanceClass_000001/overview',
    trail: [
      'Library',
      'Concepts',
      'Activities',
      'Activity Instance Classes',
      'Activity Instance Class A',
    ],
  },
  {
    path: '/library/activities/activity-item-classes/ActivityItemClass_000001/overview',
    trail: [
      'Library',
      'Concepts',
      'Activities',
      'Activity Item Classes',
      'Activity Item Class A',
    ],
  },
  {
    path: '/library/activities/activity-sub-groups/ActivitySubGroup_000001/overview',
    trail: [
      'Library',
      'Concepts',
      'Activities',
      'Activity Subgroups',
      'Activity Sub Group A',
    ],
  },

  // Studies
  { path: '/studies/summary', trail: ['Studies', 'About Studies'] },
  {
    path: '/studies/select_or_add_study',
    trail: ['Studies', 'Study List', 'Study list'],
  },
  {
    path: `/studies/${STUDY_UID}/study_status`,
    trail: ['Studies', 'Manage Study', 'Study', 'Study Core Attributes'],
  },
  {
    path: `/studies/${STUDY_UID}/data_standard_versions`,
    trail: [
      'Studies',
      'Manage Study',
      'Data Standard Versions',
      'Controlled Terminology',
    ],
  },
  {
    path: `/studies/${STUDY_UID}/study_title`,
    trail: ['Studies', 'Define Study', 'Study Title'],
  },
  {
    path: `/studies/${STUDY_UID}/registry_identifiers`,
    trail: ['Studies', 'Define Study', 'Registry Identifiers'],
  },
  {
    path: `/studies/${STUDY_UID}/study_properties`,
    trail: ['Studies', 'Define Study', 'Study Properties', 'Study Type'],
  },
  {
    path: `/studies/${STUDY_UID}/study_structure`,
    trail: ['Studies', 'Define Study', 'Study Structure', 'Overview'],
  },
  {
    path: `/studies/${STUDY_UID}/population`,
    trail: ['Studies', 'Define Study', 'Study Population'],
  },
  {
    path: `/studies/${STUDY_UID}/selection_criteria`,
    trail: ['Studies', 'Define Study', 'Study Criteria', 'CT Codelist Term A'],
  },
  {
    path: `/studies/${STUDY_UID}/study_purpose`,
    trail: ['Studies', 'Define Study', 'Study Purpose', 'Study Objectives'],
  },
  {
    path: `/studies/${STUDY_UID}/activities/list`,
    trail: ['Studies', 'Define Study', 'Study Activities', 'Study Activities'],
  },
  {
    path: `/studies/${STUDY_UID}/activities/soa`,
    trail: [
      'Studies',
      'Define Study',
      'Study Activities',
      'Schedule of Activities',
    ],
  },
  {
    path: `/studies/${STUDY_UID}/data_specifications`,
    trail: [
      'Studies',
      'Define Study',
      'Data Specifications',
      'Study Activity Instances',
    ],
  },
  {
    path: `/studies/${STUDY_UID}/protocol_elements`,
    trail: [
      'Studies',
      'View Specifications',
      'Protocol Elements',
      'Title Page',
    ],
  },
]

async function readCrumbs(page) {
  await page.locator('.v-breadcrumbs').waitFor({ timeout: 15_000 })
  // Crumb text settles after the in-page tab activates — small wait is the
  // simplest way to avoid sampling mid-render.
  await page.waitForTimeout(300)
  return page.locator('.v-breadcrumbs-item').allInnerTexts()
}

for (const { path, trail } of DEEP_LINK_CASES) {
  test(`smoke: deep-link ${path} renders the expected breadcrumb trail`, async ({
    page,
  }) => {
    await page.addInitScript(seedDemoAuth)
    const spy = setupConsoleSpy(page)
    await page.goto(path)
    expect(await readCrumbs(page)).toEqual(trail)
    spy.assertClean()
  })
}

test('smoke: cross-section navigation does not leak breadcrumbs', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)
  // Library → Studies → Library → Studies, asserting the trail at every
  // step matches a fresh deep-link.
  await page.goto('/library/activities/activities')
  expect(await readCrumbs(page)).toEqual([
    'Library',
    'Concepts',
    'Activities',
    'Activities',
  ])

  await page.goto(`/studies/${STUDY_UID}/study_title`)
  expect(await readCrumbs(page)).toEqual([
    'Studies',
    'Define Study',
    'Study Title',
  ])

  await page.goto('/library/sponsor')
  expect(await readCrumbs(page)).toEqual([
    'Library',
    'Code Lists',
    'Sponsor',
    'All',
  ])

  await page.goto(`/studies/${STUDY_UID}/activities/list`)
  expect(await readCrumbs(page)).toEqual([
    'Studies',
    'Define Study',
    'Study Activities',
    'Study Activities',
  ])
  spy.assertClean()
})

test('smoke: sidebar click path produces the same trail as a deep link', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)
  await page.goto(`/studies/${STUDY_UID}/study_status`)

  // Wait for the study to actually be selected before touching the menu.
  // Sidebar items are studyRequired: clicking one before the study store is
  // populated makes RedirectHandler pop a "no study selected" dialog instead
  // of navigating, which then stalls the waitForURL below.
  await readCrumbs(page)

  // Define Study is a parent expander (role=option, since its v-list-group
  // has an id and is therefore treated as a selectable list entry), Study
  // Activities is a real link inside it.
  const defineStudyGroup = page.locator(
    '.v-navigation-drawer .v-list-item[role="option"]',
    { hasText: 'Define Study' }
  )
  await defineStudyGroup.first().click()
  const studyActivitiesLink = page
    .locator('.v-navigation-drawer .v-list-item[role="link"]', {
      hasText: 'Study Activities',
    })
    .first()
  // Real checkpoint instead of an arbitrary wait: confirm the group's
  // expand transition actually revealed the link before clicking it.
  await expect(studyActivitiesLink).toBeVisible({ timeout: 10_000 })
  await studyActivitiesLink.click()
  // The sidebar lands on /activities, then ActivitiesPage redirects to a
  // default sub-tab (/activities/soa). Wait for the settled route with an
  // auto-retrying assertion so we don't race that redirect (or the strict
  // trailing-slash glob) — the leaf sub-tab is optional.
  await expect(page).toHaveURL(
    new RegExp(`/studies/${STUDY_UID}/activities(/(list|soa|instances))?/?$`),
    { timeout: 15_000 }
  )

  const clickedPath = new URL(page.url()).pathname
  const clickedTrail = await readCrumbs(page)

  // Assert this navigation path matches a fresh deep-link to the exact
  // destination route reached by the sidebar click.
  await page.goto(clickedPath)
  const deepLinkTrail = await readCrumbs(page)
  expect(clickedTrail).toEqual(deepLinkTrail)
  spy.assertClean()
})

test('smoke: clicking a parent breadcrumb navigates up and keeps the trail', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)
  const spy = setupConsoleSpy(page)
  await page.goto(`/studies/${STUDY_UID}/activities/soa`)
  expect(await readCrumbs(page)).toEqual([
    'Studies',
    'Define Study',
    'Study Activities',
    'Schedule of Activities',
  ])

  // The "Study Activities" crumb (index 2) is a clickable link back to the
  // tab landing page (URL drops the trailing /soa).
  await page.locator('.v-breadcrumbs-item').nth(2).locator('a').first().click()
  await expect(page).toHaveURL(
    new RegExp(`/studies/${STUDY_UID}/activities(/(list|soa|instances))?/?$`),
    { timeout: 15_000 }
  )

  // After the upward click, the trail must still represent the path back —
  // i.e. start with the same Studies → Define Study → Study Activities
  // prefix. The leaf may differ depending on whether the page redirects to
  // a default sub-tab.
  const crumbs = await readCrumbs(page)
  expect(crumbs.slice(0, 3)).toEqual([
    'Studies',
    'Define Study',
    'Study Activities',
  ])
  spy.assertClean()
})
