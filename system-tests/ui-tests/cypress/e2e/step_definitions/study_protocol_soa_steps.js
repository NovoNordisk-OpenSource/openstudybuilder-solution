const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");


Then('The Export option is visible', () => {
    cy.get('.v-row [title="Export"]').should('be.visible');
  }
)

When('The user switches the layout to {string}', (select) => {
    cy.selectAutoComplete('SoA-layout-dropdown', select)
  }
)

Then('The user is presented with {string} layout', (select) => {
    cy.get('.v-row .v-select__selection-text').contains(select).should('be.visible');
  }
)