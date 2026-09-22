const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The table {string} displays following data', (table, dataTable) => {
  cy.findInTable(table, dataTable)
})

Then('The panel {string} displays {string}', (panel, value) => {
  cy.findInPanel(panel, value)
})

Then('The panel {string} should display data', (panel) => {
  cy.panelShouldNotContain(panel, 'Query returned no data')
})


Then('The table {string} displays the following items', (table, dataTable) => {
  dataTable.hashes().forEach((element, k) => {
    if (element.value) {
      cy.get(`input[value^="${table}"]`).first().parents('.react-grid-item').first().find('.MuiDataGrid-columnHeaderTitle').eq(k).should('have.text', element.column)
      cy.get(`input[value^="${table}"]`).first().parents('.react-grid-item').first().contains(`[data-field="${element.column}"]`, element.value).should('exist')
    }
  })

})