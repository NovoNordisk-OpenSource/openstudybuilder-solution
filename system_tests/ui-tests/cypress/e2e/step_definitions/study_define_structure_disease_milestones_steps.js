const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid } = require("../../support/helper_functions");

When('Create study disease milestone button is clicked', () => cy.clickButton('create-disease-milestone'))

When('Disease mileston type is filled in', () => cy.selectAutoComplete('disease-milestone-type', 'Diagnosis of diabetes'))

Then('The new Study Disease Milestone is visible within the study disease milestones table', () => {
    cy.checkRowByIndex(0, '#','1')
    cy.checkRowByIndex(0, 'Type', 'Diagnosis of diabetes')
    cy.checkRowByIndex(0, 'Definition', 'Initial diagnosis of')
    cy.checkRowByIndex(0, 'Repetition indicator', 'No')
})

Given('[API] The test Study Disease Milestones exists', () => cy.checkAndCreateDiseaseMilestone(getCurrStudyUid()))

When('The Study Disease Milestones is edited', () => cy.get('[data-cy="repetition-indicator"] input').check())

Then('The Study Disease Milestones with updated values is visible within the table', () => cy.checkRowByIndex(0, 'Repetition indicator', 'Yes'))

Then('The validation appears under that field in the Disease Milestones form', () => {
    cy.get('.v-messages__message').should('contain', 'This field is required')
})

Then('The test Study Disease Milestones is no longer available', () => cy.contains('table tbody tr', 'Diagnosis of diabetes').should('not.exist'))