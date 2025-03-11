const { When, Then } = require('@badeball/cypress-cucumber-preprocessor')
import { getCurrentDateFormatted } from '../../support/helper_functions'


const release_description = 'Test release description'
const lock_description = 'Test lock description'
let new_version
let locked_date
let released_date

When('The study is released with description provided', () => {
  released_date = getCurrentDateFormatted()
  cy.getValueFromCellsWithIndex(0, 2).then((current_version) => {
    new_version = current_version == NaN ? 0 : parseFloat(current_version)
  })
  cy.clickButton('release-study')
  cy.fillInput('release-description', release_description)
  cy.clickButton('save-button')
  cy.waitForFormSave()
})

When('The study is locked with description provided', () => {
  locked_date = getCurrentDateFormatted()
  cy.getValueFromCellsWithIndex(0, 2).then((current_version) => {
    new_version = current_version == NaN ? 0 : parseFloat(current_version)
  })
  cy.clickButton('lock-study')
  cy.fillInput('release-description', lock_description)
  cy.clickButton('save-button')
  cy.waitForFormSave()
})

When('The study is unlocked', () => {
  cy.clickButton('unlock-study')
  released_date = getCurrentDateFormatted()
})

Then('A the first row is showing Draft without Version and description, with the current timestamp', () => {
  cy.checkRowByIndex(0, 'Study status', 'Draft')
  cy.checkRowByIndex(0, 'Version', '')
  cy.checkRowByIndex(0, 'Release description', '')
  cy.checkRowByIndex(0, 'Modified', released_date)
})

Then('A row for the Released Study Status is displayed with a current time stamp and Release description and version incremented by 0.1', () => {
  cy.checkRowByIndex(1, 'Study status', 'Released')
  cy.checkRowByIndex(1, 'Version', (new_version + 0.1).toFixed(1))
  cy.checkRowByIndex(1, 'Release description', release_description)
  cy.checkRowByIndex(1, 'Modified', released_date)
})

Then('A row for the Locked Study Status is displayed with a current time stamp and Lock description and version rounded up to full number', () => {
  cy.checkRowByIndex(0, 'Study status', 'Locked')
  cy.checkRowByIndex(0, 'Version', Math.ceil(new_version))
  cy.checkRowByIndex(0, 'Release description', lock_description)
  cy.checkRowByIndex(0, 'Modified', locked_date)
})

Then('A row for the Released Study Status is displayed with a current time stamp and Lock description and version rounded up to full number', () => {
  cy.checkRowByIndex(1, 'Study status', 'Released')
  cy.checkRowByIndex(1, 'Version', Math.ceil(new_version))
  cy.checkRowByIndex(1, 'Release description', lock_description)
  cy.checkRowByIndex(1, 'Modified', locked_date)
})
