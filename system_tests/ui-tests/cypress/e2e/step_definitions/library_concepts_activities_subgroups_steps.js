import { apiGroupName } from "./api_library_steps"
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let activitysubgroup, abbreviation = "ABB", definition = "DEF"

Then('Activity subgroup is present in first table row', () => cy.checkRowByIndex(0, 'Activity subgroup', activitysubgroup))

When('User intercepts activity subgroup request', () => cy.intercept('/api/concepts/activities/activity-sub-groups?page_number=1&*').as('getData'))

When('User waits for activity subgroup request', () => cy.wait('@getData', {timeout: 20000}))

When('The Add activity subgroup button is clicked', () => cy.clickButton('add-activity'))

When('Activity subgroup is searched for and found', () => cy.searchAndCheckPresence(activitysubgroup, true))

When('Activity subgroup is searched for and not found', () => cy.searchAndCheckPresence(activitysubgroup, false))

When('The activity subgroup edition form is filled with data', () => editSubGroup())

When('The activity subgroup form is filled with data', () => fillSubGroupData())

Then('The newly added activity subgroup is visible in the the table', () => {  
    cy.checkRowByIndex(0, 'Activity subgroup', activitysubgroup)
    cy.checkRowByIndex(0,'Sentence case name', activitysubgroup.toLowerCase())
    cy.checkRowByIndex(0, 'Abbreviation', abbreviation)
    cy.checkRowByIndex(0, 'Definition', definition)
})

When('The Activity Subgroup name, Sentence case name and Definition fields are not filled with data', () => {
    cy.fillInput('groupform-activity-group-field', 'test')
    cy.clearInput('sentence-case-name-field')
    cy.clearInput('groupform-activity-group-field')
})

Then('The user is not able to save the acitivity subgroup', () => {   
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('span.dialog-title').should('be.visible').should('have.text', 'Add activity subgroup'); 
})

Then('The validation appears for missing subgroup', () => cy.checkIfValidationAppears('groupform-activity-group-field'))

Then('The validation appears for missing subgroup name', () => cy.checkIfValidationAppears('sentence-case-name-class'))

Then('The validation appears for missing subgroup definition', () => cy.checkIfValidationAppears('groupform-definition-class'))

When('The user enters a value for Activity subgroup name', () => {
    cy.fillInput('groupform-activity-group-field', "TEST")
})

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity subgroup name', () => {      
    cy.get('[data-cy="sentence-case-name-field"] input').should('have.value', 'test')
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity subgroup name', () => {
    cy.fillInput('groupform-activity-group-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
})

When('[API] Activity subgroup in status Draft exists', () => createSubGroupViaApi())

When('[API] Activity subgroup is approved', () => cy.approveSubGroup())

When('[API] Activity subgroup is inactivated', () => cy.inactivateSubGroup())

When('[API] Activity subgroup is reactivated', () => cy.reactivateSubGroup())

When('[API] Activity subgroup gets new version', () => cy.subGroupNewVersion())

Given('[API] First activity subgroup for search test is created', () => createSubGroupViaApi(`SearchTest${getShortUniqueId()}`))

Given('[API] Second activity subgroup for search test is created', () => cy.createSubGroup(`SearchTest${getShortUniqueId()}`))

Given('[API] Activity subgroup is created', () => cy.createSubGroup())

function fillSubGroupData() {
    cy.get('[data-cy="groupform-activity-group-field"] input').click().type(activitysubgroup = `Subgroup${getShortUniqueId()}`)
    cy.fillInput('groupform-abbreviation-field', abbreviation)
    cy.fillInput('groupform-definition-field', definition)
}

function editSubGroup() {
    cy.get('[data-cy="groupform-activity-group-field"] input').should('have.value', activitysubgroup)
    cy.get('[data-cy="groupform-activity-group-field"] input').click().clear().type(activitysubgroup = `${activitysubgroup}Edited`)
    cy.fillInput('groupform-change-description-field', "e2e test")
}

function createSubGroupViaApi(customName = '') {
    cy.createSubGroup(customName)
    cy.getSubGroupNameByUid().then(name => activitysubgroup = name)
}