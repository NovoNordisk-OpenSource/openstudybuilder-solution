const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')
import { getCurrStudyUid } from '../../support/helper_functions'

let study_number

Given('[API] Study title is set for selected study', () => cy.setStudyTitle(getCurrStudyUid(), 'test title', 'test short title'))

Given('[API] Status of study is checked and locked in major version {string} and minor version {string}', (major_version, minor_version) => {
  cy.checkStatusAndLock(getCurrStudyUid(), major_version, minor_version)
})

Given('[API] Status of study is checked and unlocked in major version {string} and minor version {string}', (major_version, minor_version) => {
  cy.checkStatusAndUnLock(getCurrStudyUid(), major_version, minor_version)
})

Given('[API] Status of study is checked and unlocked, keeping the existing version', () => {
  cy.checkStatusAndUnLockKeepingTheVersion(getCurrStudyUid())
})

Given('[API] Status of study is checked and locked, keeping the existing version', () => {
  cy.checkStatusAndLockKeepingTheVersion(getCurrStudyUid())
})

Given('User sets reson for change of study status to {string}', (value) => cy.selectVSelect('change-reason', value))

When("The user provides explanation for other reason", () => cy.fillTextBox('lock-release-other-reason', 'Test reason'))

When("The user provides release description", () => cy.fillInput('release-description', 'Test description'))

Given('User clicks lock study button', () => cy.clickButton('lock-study'))

Given('User clicks unlock study button', () => cy.clickButton('unlock-study'))

When('The lock study request is intercepted', () => cy.intercept('**/locks').as('lockRequest'))

When('The unlock study request is intercepted', () => cy.intercept('**/unlocks').as('unlockRequest'))

When('The study snapshot request is intercepted', () => cy.intercept(`**/studies/${getCurrStudyUid()}/snapshot-history?*`).as('snapshot'))

When('The study protocol request is intercepted', () => cy.intercept(`**/studies/${getCurrStudyUid()}/protocol-header-versions?*`).as('protocol'))

When('User waits for lock study request', () => cy.wait('@lockRequest'))

When('User waits for unlock study request', () => cy.wait('@unlockRequest'))

When('User waits for study snapshot request', () => cy.wait('@snapshot'))

When('User waits for study protocol request', () => cy.wait('@protocol'))

When("The user provides protocol major version {string}", (major_version) => {
  cy.get('[data-cy="major-version"]').clear().type(major_version)
})

When("The user provides protocol minor version {string}", (minor_version) => {
  cy.get('[data-cy="minor-version"]').clear().type(minor_version)
})

Then('The procotol version is displayed in table as {string}', (value) => cy.checkRowByIndex(0, 'Protocol Version', value))

Then('The study is displayed as unlocked with {string} as a reason', (reason) => cy.checkRowByIndex(0, 'Reason for unlocking study', reason))

Then('The study is displayed as locked with {string} as a reason', (reason) => cy.checkRowByIndex(0, 'Reason for locking or releasing study', reason))

Then('[API] User fetches term uid for reason for locking {string}', (reason) => cy.getReasonForLockingTermUid(reason))

Then('[API] User fetches term uid for reason for unlocking {string}', (reason) => cy.getReasonForUnLockingTermUid(reason))