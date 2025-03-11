Cypress.Commands.add('elementContain', (selector, text) => {
    cy.get(`[data-cy="${selector}"]`).should('contain', text)
})

Cypress.Commands.add('checkSnackbarMessage', (message) => {
    cy.get('.v-snackbar__content').should('contain', message).and('be.visible')
})

Cypress.Commands.add('warningIsDisplayedForField', (fieldLocator, message) => {
    cy.get(fieldLocator).contains('.v-messages__message', message).should('be.visible'); 
})
