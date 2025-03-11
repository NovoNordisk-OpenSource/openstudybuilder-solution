Cypress.Commands.add('clickFirstButton', (button, optionForce = false) => {
    cy.get('[data-cy="' + button + '"]')
        .first()
        .click({ force: optionForce })
})

Cypress.Commands.add('clickButton', (button, optionForce = true) => {
    cy.get('[data-cy="' + button + '"]').click({ force: optionForce })
})

Cypress.Commands.add('clickFormActionButton', (action) => {
    cy.get(`.v-card-actions [data-cy="${action.toLowerCase()}-button"]`).click({ force: true })
    cy.wait(1500)
})

Cypress.Commands.add('clickByIndex', (button, index, optionForce = true) => {
    cy.get('[data-cy="' + button + '"]').eq(index).click({ force: optionForce })
})

Cypress.Commands.add('toggleButton', (button, optionForce = true, optionMultiple = false) => {
    cy.get('[data-cy="' + button + '"]').click({ force: optionForce, multiple: optionMultiple })
})

Cypress.Commands.add('toggleFirstButton', (button, optionForce = true, optionMultiple = false) => {
    cy.get('[data-cy="' + button + '"]').first().click({ force: optionForce, multiple: optionMultiple })
})

Cypress.Commands.add('clickTab', (tabName, optionForce = 'true') => {
    cy.contains('.v-tab', tabName).click({ force: optionForce })
})

Cypress.Commands.add('checkAllCheckboxes', () => {
    cy.wait(1000)
    cy.get('[data-cy="not-applicable-checkbox"]').each((btn) => {
        cy.get(btn).within(() => {
            cy.get('[type="checkbox"]').click({ force: true })
        })
    })
})

Cypress.Commands.add('checkbox', (button, optionForce = true, optionMultiple = false) => {
    cy.get('[data-cy="' + button + '"]').within(() => {
        cy.get('input').click({ force: optionForce, multiple: optionMultiple })
    })
})