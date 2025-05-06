Cypress.Commands.add('elementContain', (selector, text) => {
    cy.get(`[data-cy="${selector}"]`).should('contain', text)
})

Cypress.Commands.add('checkSnackbarMessage', (message) => {
    cy.get('.v-snackbar__content').should('contain', message).and('be.visible')
})

Cypress.Commands.add('checkIfValidationAppears', (locator, message = 'This field is required') => {
    cy.elementContain(locator, message)
})

Cypress.Commands.add('checkIfValidationNotPresent', (locator, message = 'This field is required') => {
    cy.contains(`[data-cy="${locator}"]`, message).should('not.exist')
})

