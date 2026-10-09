const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let studyAcronym

Given('User intercepts request with available studies', () => cy.intercept('/api/studies?page_size=0').as('availableStudies'))

Given('User waits for request with available studies', () => cy.wait('@availableStudies'))

Given('User clicks edit content button', () => cy.get('[data-cy="edit-content"]').click())

Given('Edit Study Attributes window is opened', () => cy.contains('.dialog-title', 'Edit study').should('be.visible'))

Given('The Project name input field is disabled for edition', () => cy.get('.v-input--disabled[data-cy="project-name"]').should('exist'))

Given('The Brand name input field is disabled for edition', () => cy.get('.v-input--disabled[data-cy="brand-name"]').should('exist'))

Given('The Study ID input field is disabled for edition', () => cy.get('.v-input--disabled[data-cy="study-id"]').should('exist'))

Given('The Study Acronym value is updated with {string}', (value) => {
    cy.get('[data-cy="study-acronym"] input').type(` ${value}`).invoke('val').then(val => studyAcronym = val)
})

Given('The Study Acronym value is visible in the table', () => {
    cy.contains('table tbody tr', 'Study acronym').find('td').eq(1).should('have.text', studyAcronym)
})