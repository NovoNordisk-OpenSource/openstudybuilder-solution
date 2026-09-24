Cypress.Commands.add('clickFirstButton', (button) => cy.get(`[data-cy="${button}"]`).first().click())

Cypress.Commands.add('clickButton', (button, optionForce = true) => cy.get(`[data-cy="${button}"]`).click({ force: optionForce }))

Cypress.Commands.add('clickFormActionButton', (action) => {
    cy.get(`.v-card-actions [data-cy="${action.toLowerCase()}-button"]`).click({ force: true })
    cy.get(`.v-card-actions [data-cy="${action.toLowerCase()}-button"] .v-progress-circular`, { timeout: 30000 }).should('not.exist') 
    if (action != 'save') cy.wait(1500)
})

Cypress.Commands.add('selectRadioButton', (name, value) => cy.get(`[data-cy="${name}"] [data-cy="radio-${value}"] input`).click())

Cypress.Commands.add('selectDatePicker', (field, day) => {
    cy.get(`[data-cy="${field}"]`).click()
    cy.get(`[data-cy="${field}-picker"]`).contains('.v-btn__content', day).click()
})

Cypress.Commands.add('setDuration', (field, value, unit) => {
    cy.get(`[data-cy="${field}"]`).within(() => {
        cy.fillInput('duration-value', value)
        cy.get('[data-cy="duration-unit"]').click()
    })
    cy.get('.v-list').filter(':visible').contains('.v-list-item', unit).click()
})