import { fillTemplateName } from './library_syntax_templates_common_steps'
const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')
const { getShortUniqueId } = require("../../support/helper_functions");

let defaultEndpointName

When('The endpoint template is found', () => cy.searchAndCheckPresence(defaultEndpointName, true))

When('The endpoint template is not found', () => cy.searchAndCheckPresence(defaultEndpointName, false))

When('The endpoint template is not updated', () => cy.searchAndCheckPresence(defaultEndpointName, false))

Then('The endpoint template name is displayed in the table', () => cy.checkRowByIndex(0, 'Parent template', defaultEndpointName))

Then('The endpoint template name is checked', () => cy.get('[data-cy="template-text-field"] [id="editor"]').invoke('text').should('equal', defaultEndpointName))

When('The endpoint template form is filled with base data', () => fillBaseData(`Endpoint${getShortUniqueId()}`))

When('The endpoint metadata update is started', () => fillBaseData(`Update${getShortUniqueId()}`))

When('The endpoint template edition form is filled with data', () => fillBaseData(`CancelEdit${getShortUniqueId()}`))

When('The endpoint template form is filled with already existing name', () => fillBaseData(defaultEndpointName))

When('[API] Endpoint template is inactivated', () => cy.inactivateEndpoint())

When('[API] Approve endpoint template', () => cy.approveEndpoint())

When('[API] Create endpoint template', () => {
  createEndpointViaApi()
  cy.getEndpointName().then(name => defaultEndpointName = name.replace('<p>', '').replace('</p>', '').trim())
})

When('[API] Search Test - Create first endpoint template', () => {
  defaultEndpointName = `SearchTest${getShortUniqueId()}`
  createEndpointViaApi(defaultEndpointName)
})

When('[API] Search Test - Create second endpoint template', () => createEndpointViaApi(`SearchTest${getShortUniqueId()}`))

function createEndpointViaApi(customName = '') {
  cy.getInidicationUid()
  cy.getEndpointCategoryUid()
  cy.getEndpointSubCategoryUid()
  cy.createEndpoint(customName)
}

function fillBaseData(endpointName) {
  defaultEndpointName = endpointName
  fillTemplateName(defaultEndpointName)
}