const { When, Then } = require('@badeball/cypress-cucumber-preprocessor')

When('expand table and Show SoA groups is available on the page', () => {
    cy.get('.mb-4').should('contain', 'Expand table')
    cy.get('.mb-4').should('contain', 'Show SoA groups')
})
