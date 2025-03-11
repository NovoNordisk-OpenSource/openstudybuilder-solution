Cypress.Commands.add('selectDatePicker', (field, day) => {
    cy.clickButton(field)
    cy.get('[data-cy=' + field + '-picker]').within(() => {
        cy.contains('.v-btn__content', day).click()

    })
})