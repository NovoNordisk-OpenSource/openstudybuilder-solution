Cypress.Commands.add('setDuratinField', (field, value, unit) => {
    cy.get('[data-cy="' + field + '"]').within(() => {
        cy.fillInput('duration-value', value)
        cy.get('[data-cy="duration-unit"]').within(() => {
            cy.get('.v-field__input').click()
        })
    })
    cy.get('.v-list')
        .filter(':visible')
        .within(() => {
            cy.get('.v-list-item').contains(unit).click()
        })
})