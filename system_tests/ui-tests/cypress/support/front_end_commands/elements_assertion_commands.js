Cypress.Commands.add('checkSnackbarMessage', (message) => {
    cy.get('.v-alert').should('contain', message).and('be.visible')
})

Cypress.Commands.add('checkIfValidationAppears', (selector, message = 'This field is required') => {
    cy.get(`[data-cy="${selector}"]`).should('contain', message)
})

Cypress.Commands.add('checkIfValidationNotPresent', (locator, message = 'This field is required') => {
    cy.contains(`[data-cy="${locator}"]`, message).should('not.exist')
})
