Cypress.Commands.add('selectRadio', (field, value) => {
    cy.get('[data-cy="' + field + '"]').within(() => {
        cy.get('[data-cy="radio-' + value + '"]').within(() => {
            cy.get('input').click()
        })
    })
})

Cypress.Commands.add('selectRadioGroup', (field, value) => {
    cy.get('[data-cy="' + field + '"]').within(() => {
        cy.contains(value).click()
    })
})