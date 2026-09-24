const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user click SHOWN DETAIL in the {string} table', (table) => {
  cy.get(`input[value^="${table}"]`).first()
    .parents('.react-grid-item').first()
    .contains('SHOWN DETAIL')
    .click({ force: true })
  cy.wait(500)
})



