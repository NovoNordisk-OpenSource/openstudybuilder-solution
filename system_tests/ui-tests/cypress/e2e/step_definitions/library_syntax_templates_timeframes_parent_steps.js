const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let timeframeName, timeframeNameWithParameter

Then('The timeframe template is found', () => cy.searchAndCheckPresence(timeframeName, true))

Then('The timeframe template is not found', () => cy.searchAndCheckPresence(timeframeName, false))

Then('The Timeframe is visible in the Table', () => cy.checkRowByIndex(0, 'Template', timeframeName))

Then('The Timeframe with paramter is visible in the Table', () => cy.checkRowByIndex(0, 'Template', timeframeNameWithParameter))

When('Change description for timeframe template is provided', () => cy.contains('.v-input', 'Change description').type('ok'))

When('Change description for timeframe template is cleared', () => cy.contains('.v-input', 'Change description').clear())

Then("The validation appears for timeframe change description field", () => cy.contains('.v-input', 'Change description').should('contain', 'This field is required'))

Then("The validation appears for timeframe name field", () => cy.get('.v-overlay .v-input').should('contain', 'This field is required'))

When('The timeframe template form is filled with base data', () => fillBaseData(`Timeframe${getShortUniqueId()}`))

When('The timeframe template metadata update is started', () => fillBaseData(`Update${getShortUniqueId()}`))

When('The timeframe template edition form is filled with data', () => fillBaseData(`CancelEdit${getShortUniqueId()}`))

When('The second timeframe is added with the same template text', () => fillBaseData(timeframeName))

Then('[API] Timeframe template in status Draft exists', () => createTimeframeTemplateViaApi())

Then('[API] Timeframe template is approved', () => cy.approveTimeframe())

Then('[API] Timeframe template is inactivated', () => cy.inactivateTimeframe())

Then('[API] Timeframe template gets new version', () => cy.newVersionOfTimeframe(timeframeName))

When('[API] Search Test - Create first timeframe template', () => {
  timeframeName = `SearchTest${getShortUniqueId()}`
  createTimeframeTemplateViaApi(timeframeName)
})

When('[API] Search Test - Create second timeframe template', () => createTimeframeTemplateViaApi(`SearchTest${getShortUniqueId()}`))

Then('Timeframe template created via API is searched for', () => {
  cy.intercept('/api/timeframe-templates?page_number=1&*').as('getTemplate')
  cy.wait('@getTemplate', {timeout: 20000})
  cy.searchAndCheckPresence(timeframeName, true)
})

When('Timeframe template text type is selected', () => {
  cy.get('[data-cy="input-field"]').type(' ');
  cy.get('[data-cy="types-dropdown"] .v-list-item').first().click()
  cy.get('[id="editor"]').invoke('text').then(text => timeframeNameWithParameter = text.replace('[', '').replace(']', ''))
})

Then('The History for template window is displayed', () => {
  cy.get(`[data-cy="version-history-window"]`).should('be.visible');
  cy.get('.dialog-title').contains('History for template')
})

function createTimeframeTemplateViaApi(customName = '') {
  cy.createTimeframe(customName)
  cy.getTimeframeName().then(name => timeframeName = name.replace('<p>', '').replace('</p>', '').trim())
}

function fillBaseData(name) {
  cy.wait(1000)
  timeframeName = name
  cy.get('[data-cy="input-field"]').type(timeframeName);
}