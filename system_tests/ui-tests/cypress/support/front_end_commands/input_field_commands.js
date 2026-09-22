Cypress.Commands.add('fillInput', (inputField, value) => {
    cy.get(`[data-cy="${inputField}"] .v-field__input`).first().clear({ force: true }).type(value)
})

Cypress.Commands.add('fillInputNew', (inputField, value) => cy.get(`[data-cy="${inputField}"] input`).clear().type(value))

Cypress.Commands.add('fillTextArea', (textArea, value) => {
    cy.get(`[data-cy="${textArea}"]`).within(() => {
    cy.get('[data-cy="input-field"] > .ql-editor').clear({ force: true }).type(value)})
})

Cypress.Commands.add('fillTextBox', (textArea, value) => {
    cy.get(`[data-cy="${textArea}"]`).type(value)
})

Cypress.Commands.add('clearField', (fieldName) => {
    cy.get(`[data-cy="${fieldName}"] .mdi-close-circle`).click({force: true})
})

Cypress.Commands.add('clearInput', (fieldName) => {
    cy.get(`[data-cy="${fieldName}"] input`).clear({force: true})
})

Cypress.Commands.add('clearSearchField', () => {
    cy.get('[data-cy="search-field"]').within(() => {
        cy.get('.v-field__input').clear({force: true})
    })
})

Cypress.Commands.add('checkIfInputDisabled', (locatorValue) => {
    cy.get(`[data-cy="${locatorValue}"]`).within(() => {
        cy.get('input').should('have.attr', 'disabled')
    })
})