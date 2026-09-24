const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let apiRequestedActivityName

Then('The add activity request button is not available', () => cy.get('add-activity').should('not.exist'))

Then('The validation message appears for sentance case name', () => cy.checkIfValidationAppears('sentence-case-name-field'))

When('The user clear default value from Sentance case name', () => cy.clearInput('sentence-case-name-field'))

Then('One activity request is found after performing full name search', () => cy.searchAndCheckPresence(apiRequestedActivityName, true))

Then('Requested activity is found', () => cy.searchAndCheckPresence(apiRequestedActivityName, true))

When('The request continue button is clicked', () => cy.clickButton('step.request-continue-button'))

When('The sponsor continue button is clicked', () => cy.clickButton('step.sponsor-continue-button'))

When('The confirm continue button is clicked', () => cy.clickButton('step.confirm-continue-button'))

When('[API] Requested activity in status Draft exists', () => createRequestedActivityViaApi())

When('[API] Requested activity is approved', () => cy.approveRequestedActivity())

When('[API] Requested activity is inactivated', () => cy.inactivateRequestedActivity())

Given('[API] First requested activity for search test is created', () => createRequestedActivityViaApi(`SearchTest${getShortUniqueId()}`))

Given('[API] Second requested activity for search test is created', () => cy.createRequestedActivity(true, `SearchTest${getShortUniqueId()}`))

function createRequestedActivityViaApi(customName = '') {
    cy.intercept('/api/concepts/activities/activities?page_number=1&*').as('getData')
    cy.getFinalGroupUid()
    cy.getFinalSubGroupUid()
    cy.createRequestedActivity(true, customName)
    cy.getRequestedActivityNameByUid().then(name => apiRequestedActivityName = name)
    cy.wait('@getData', {timeout: 20000})
}