Cypress.Commands.add('fillInput', (inputField, value) => {
    cy.get(`[data-cy="${inputField}"]`).first().within(() => {
        cy.get('[class="v-field__input"]').clear({ force: true }).type(value, { force: true })
        cy.wait(1000)
    })
})

Cypress.Commands.add('fillInputNew', (inputField, value) => {
    cy.get(`[data-cy="${inputField}"] input`).clear().type(value)
    cy.wait(1000)
})

Cypress.Commands.add('fillTextArea', (textArea, value) => {
    cy.get(`[data-cy="${textArea}"]`).within(() => {
    cy.get('[data-cy="input-field"] > .ql-editor')
    .clear({ force: true })
    .type(value, { force: true })
    })
    cy.wait(1000)
})

Cypress.Commands.add('clearField', (fieldName) => {
    cy.get(`[data-cy="${fieldName}"]`).within(() => {
        cy.get('.mdi-close-circle').click({force: true})
    })
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