Cypress.Commands.add('getText', (locator) => {
    cy.get(locator).invoke('text').then(text => { return text })
})