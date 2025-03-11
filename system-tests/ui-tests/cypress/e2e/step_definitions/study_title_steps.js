const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let studyTitle

When('The study title form is filled with new title and saved', () => {
    cy.wait(1500)
    cy.fillInput('study-title', 'New title')
    cy.fillInput('short-study-title', 'New short tile')
    cy.clickButton('save-button')
})

Then('The study selected has new title appended', () => {
    cy.get('[data-cy="study-title-field"]').eq(0).should('contain', 'New title')
})

Then('The study selected has new title copied', () => {
    cy.elementContain('study-title-field', studyTitle)
})

When('The study title is copied from another study', () => {
    cy.getValueFromCellsWithIndex(0, 4).then((copiedTitle) => studyTitle = copiedTitle)
    cy.clickFirstButton('copy-title')
    cy.clickButton('save-button')
})