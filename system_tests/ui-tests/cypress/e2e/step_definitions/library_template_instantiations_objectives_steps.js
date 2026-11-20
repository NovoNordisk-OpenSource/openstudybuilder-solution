const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The CLOSE button is clicked', () => {    
    cy.get('.v-btn__content').contains('Close').click()
    })
  
Then('The History page is displayed', () => {
    cy.get(`[data-cy="version-history-window"]`).should('exist');
  })
  
Then('The following column list with values will exist', (headers) => {
  cy.get('button.v-btn--loading').should('not.exist')
  headers.rows().forEach((header) => cy.get('table thead').eq(1).should('contain', header))
})

Then('The history table is not empty', () => cy.get('[data-cy="version-history-window"] table tbody tr').should('exist').should('not.contain.text', 'No data available'))

Then('The table is not empty', () => cy.get('table tbody tr').should('exist')) 

Then('The List of studies with a specific objective window is displayed', () => {
    cy.get('.dialog-title').should('contain', 'List of studies with a specific objective')
  })
