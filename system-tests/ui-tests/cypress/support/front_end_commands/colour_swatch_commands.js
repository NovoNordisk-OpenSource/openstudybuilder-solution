Cypress.Commands.add('chooseColourSwatch', (colour) => {
    cy.get('[data-cy="epoch-color-picker"]').within(() => {
        cy.get('div[style="background: rgb(' + colour + ');"]').click()
    })
})

Cypress.Commands.add('getColour', (colour) => {
    cy.get('tbody').within(() => {
        cy.get(
            'span[style="background-color: rgb(' +
            colour +
            '); border-color: rgb(' +
            colour +
            ');"]'
        ).should('exist')
    })
})