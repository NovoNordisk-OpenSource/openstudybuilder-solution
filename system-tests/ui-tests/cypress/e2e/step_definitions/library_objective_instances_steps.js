const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Given('The test objective instance exists in the table list', () => {
    cy.get('table tbody tr').should('exist');
  }) 

When('The three dots menu list clicked for the test instance', () => {
  cy.clickFirstButton('table-item-action-button')
  })

When('The {string} option is clicked', (option) => {    
  cy.get('[data-cy="' + option + '"]').contains(option).click()
  })

When('The CLOSE button is clicked', () => {    
    cy.get('.v-btn__content').contains('Close').click()
    })
  
Then('The History for objective window is displayed', () => {
    cy.get(`[data-cy="version-history-window"]`).should('exist');
  })

Then('The following column list with values will exist', (headers) => {
  cy.get('button.v-btn--loading').should('not.exist')
  headers.rows().forEach((header) => cy.get('table thead').eq(1).should('contain', header))
})

Then('The table is not empty', () => {
  cy.get('table tbody tr').should('exist');
}) 

Then('The {string} option is not available for the objective instance', (option) => {
    cy.get('.v-list-item__content').should('not.contain', option)
    cy.get('.v-list-item__content').should('contain', 'History') //To make sure it is searching in the correct place
  })

Then('The List of studies with a specific objective window is displayed', () => {
    cy.get('.dialog-title').should('contain', 'List of studies with a specific objective')
  })
