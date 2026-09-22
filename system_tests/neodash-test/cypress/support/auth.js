Cypress.Commands.add('prepareAuthTokens', () => {
    cy.exec('node token.js', {failOnNonZeroExit: false}).then((data) => {
        Cypress.env('NEODASH_ACCESS_TOKEN', data.stdout)
    })
})