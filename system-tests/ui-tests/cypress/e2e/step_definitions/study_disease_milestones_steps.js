const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The new Study Disease Milestone is added', () => {
    cy.clickButton('create-disease-milestone')
    cy.selectAutoComplete('disease-milestone-type', 'Diagnosis of diabetes')
    cy.clickButton('save-button')
})

Then('The new Study Disease Milestone is visible within the study disease milestones table', () => {
    cy.checkRowByIndex(0, '#','1')
    cy.checkRowByIndex(0, 'Type', 'Diagnosis of diabetes')
    cy.checkRowByIndex(0, 'Definition', 'Initial diagnosis of')
    cy.checkRowByIndex(0, 'Repetition indicator', 'No')
})

Given('The test Study Disease Milestones exists', () => {
    cy.checkAndCreateDiseaseMilestone()
})

When('The Study Disease Milestones is edited', () => {
    cy.waitForTableData()
    cy.tableRowActions(0, 'Edit')
    cy.wait(1500)
    cy.checkbox('repetition-indicator')
    cy.clickButton('save-button')
    cy.checkSnackbarMessage('Disease milestone updated')
})

Then('The Study Disease Milestones with updated values is visible within the table', () => {
    cy.wait(500)
    cy.checkRowByIndex(0, 'Repetition indicator', 'Yes')
})

When('The user tries to close the form without Disease Milestone Type provided', () => {
    cy.waitForTableData()
    cy.clickButton('create-disease-milestone')
    cy.clickButton('save-button')
})

Then('The validation appears under that field in the Disease Milestones form', () => {
    cy.get('.v-messages__message').should('contain', 'This field is required')
})

When('New Disease Milestone Type is created with the same Disease Milestone Type', () => {
    cy.clickButton('create-disease-milestone')
    cy.selectAutoComplete('disease-milestone-type', 'Diagnosis of diabetes')
    cy.clickButton('save-button')
})

When('The delete action is clicked for the test Study Disease Milestones', () => {
    cy.waitForTableData()
    cy.tableRowActions(0, 'Delete')
})

Then('The test Study Disease Milestones is no longer available', () => {
    cy.checkSnackbarMessage('Disease milestone deleted')
    cy.wait(1000)
    cy.get('tbody').should('not.contain', 'Diagnosis of diabetes')
})