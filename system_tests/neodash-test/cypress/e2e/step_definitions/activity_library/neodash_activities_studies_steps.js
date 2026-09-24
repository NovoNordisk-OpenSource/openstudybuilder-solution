const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user selects one study by clicking the Trial ID in the table {string}', (table) => {
  cy.get(`input[value^="${table}"]`, { timeout: 20000 })
    .first()
    .parents('.react-grid-item')
    .first()
    .find('[role="gridcell"][data-field="Trial ID"] button')
    .first()
    .click()
  cy.wait(500)
})
