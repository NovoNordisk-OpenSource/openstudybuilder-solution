const CARD_LOOKUP_TIMEOUT = 40000

Cypress.Commands.add('selectFromDropdown', (dropdownName, value) => {
    cy.contains('.MuiCardContent-root', dropdownName, { timeout: CARD_LOOKUP_TIMEOUT }).within(() => {
        cy.get('input').should('not.be.disabled').type(value)
      })
      cy.contains('[id^=autocomplete-option]', value).click()
})

Cypress.Commands.add('selectFromField', (dropdownName, value) => {
    cy.contains('.MuiCardContent-root', dropdownName, { timeout: CARD_LOOKUP_TIMEOUT }).within(() => {
        cy.get('input').should('not.be.disabled').click()
      })
      cy.contains('[id^=autocomplete-option]', value).click()
})

Cypress.Commands.add('clearDropdown', (dropdownName) => {
  cy.contains('.MuiCardContent-root', dropdownName, { timeout: CARD_LOOKUP_TIMEOUT }).within(() => {
      cy.get('[title="Clear"]').click({force: true})
    })
})
