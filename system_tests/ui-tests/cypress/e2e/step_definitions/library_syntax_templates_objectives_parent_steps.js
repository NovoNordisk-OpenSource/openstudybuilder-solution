import { fillTemplateName } from './library_syntax_templates_common_steps'
const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')
const { getShortUniqueId } = require("../../support/helper_functions");

let defaultObjectiveName

When('The objective template is found', () => cy.searchAndCheckPresence(defaultObjectiveName, true))

When('The objective template is not found', () => cy.searchAndCheckPresence(defaultObjectiveName, false))

When('The objective template is not updated', () => cy.searchAndCheckPresence(defaultObjectiveName, false))

Then('The objective template name is displayed in the table', () => cy.checkRowByIndex(0, 'Parent template', defaultObjectiveName))

Then('The objective template name is checked', () => cy.get('[data-cy="template-text-field"] [id="editor"]').invoke('text').should('equal', defaultObjectiveName))

When('The objective template form is filled with base data', () => fillBaseData(`Objective${getShortUniqueId()}`))

When('The objective metadata update is started', () => fillBaseData(`Update${getShortUniqueId()}`))

When('The objective template edition form is filled with data', () => fillBaseData(`CancelEdit${getShortUniqueId()}`))

When('The second objective is added with the same template text', () => fillBaseData(defaultObjectiveName))

When('[API] Objective template is inactivated', () => cy.inactivateObjective())

When('[API] Approve objective template', () => cy.approveObjective())

When('[API] Create objective template', () => {
  createObjectiveViaApi()
  cy.getObjectiveName().then(name => defaultObjectiveName = name.replace('<p>', '').replace('</p>', '').trim())
})

When('[API] Search Test - Create first objective template', () => {
  defaultObjectiveName = `SearchTest${getShortUniqueId()}`
  createObjectiveViaApi(defaultObjectiveName)
})

When('[API] Search Test - Create second objective template', () => createObjectiveViaApi(`SearchTest${getShortUniqueId()}`))

function createObjectiveViaApi(customName = '') {
  cy.getInidicationUid()
  //cy.getObjectiveCategoryUid()
  cy.createObjective(customName)
}

function fillBaseData(name) {
  defaultObjectiveName = name
  fillTemplateName(name)
}