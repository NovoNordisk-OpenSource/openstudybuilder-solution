const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let studyTitle

When('The study title form is filled with new title', () => {
    cy.wait(1500)
    cy.fillInput('study-title', 'New title')
    cy.fillInput('short-study-title', 'New short tile')
})

When('User sets study title as {string}', (value) => cy.fillInput('study-title', value))

When('User sets study short title as {string}', (value) => cy.fillInput('short-study-title', value))

When('The study title is displayed as {string}', (value) => cy.get('[data-cy="study-title-field"]').eq(0).should('have.text', value))

When('The study short title is displayed as {string}', (value) => cy.get('[data-cy="study-title-field"]').eq(1).should('have.text', value))

Then('The study selected has new title appended', () => {
    cy.get('[data-cy="study-title-field"]').eq(0).should('contain', 'New title')
})

Then('The study selected has new title copied', () => cy.get('[data-cy="study-title-field"]').should('contain', studyTitle))

When('The study title is copied from another study', () => {
    cy.contains('table thead th', 'Study title').should('be.visible')
    cy.waitForTableData()
    cy.getCellValueNoVisibilityCheck(0, 'Study title').then((copiedTitle) => studyTitle = copiedTitle)
    cy.clickFirstButton('copy-title')
})