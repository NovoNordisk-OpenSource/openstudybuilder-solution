const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('Modal window form is closed by clicking cancel button', () => {
    cy.get('[data-cy="form-body"] [data-cy="cancel-button"]').click()
})

When('Fullscreen wizard is closed by clicking cancel button', () => {
    cy.contains('[data-cy="form-body"].fullscreen-dialog .v-card-actions button', 'Cancel').click()
})

When('Action is confirmed by clicking continue', () => cy.clickButton('continue-popup'))

Then('The form is no longer available', () => cy.get('[data-cy="form-body"]').should('not.exist'))

When('{string} button is clicked on form', (buttonName) => cy.clickFormActionButton(buttonName))
