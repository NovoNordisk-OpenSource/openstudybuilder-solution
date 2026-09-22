import { test, expect } from '@playwright/test'
import { setupConsoleSpy } from '../helpers/consoleSpy.js'
import { seedDemoAuth } from '../helpers/seedAuth.js'

const SEED_STUDY_UID = 'Study_000001'

test('smoke: StudyStatus (study-required route) renders without crashes', async ({
  page,
}) => {
  await page.addInitScript(seedDemoAuth)

  const spy = setupConsoleSpy(page)

  await page.goto(`/studies/${SEED_STUDY_UID}/study_status`)

  await expect(page.locator('.page-title').first()).toBeVisible({
    timeout: 15_000,
  })

  spy.assertClean()
})
