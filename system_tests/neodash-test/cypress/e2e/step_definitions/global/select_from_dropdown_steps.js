const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user selects {string} from the {string} dropdown', (value, dropdown) => {
  cy.selectFromDropdown(dropdown, value)
})

When('The user selects a value from the {string} dropdown', (dropdown) => {
  cy.contains('.MuiCardContent-root', dropdown).within(() => {
    cy.get('input').should('not.be.disabled').click()
  })
  cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').first().should('be.visible').click()
})

When('The user selects {string} from the {string} field', (value, dropdown) => {
  cy.selectFromField(dropdown, value)
})


When('The user resets the {string} selector to blank', (dropdown) => {
  cy.clearDropdown(dropdown)
})

When('The user selects {string} in the {string} table', (value, table) => {
  cy.selectFromSelectorTable(table, value)
})