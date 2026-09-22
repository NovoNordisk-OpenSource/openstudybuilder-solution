const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user selects an activity instance from the {string} dropdown', (dropdown) => {
  cy.contains('label', dropdown).parents('.MuiAutocomplete-root').first().within(() => {
    cy.get('.MuiInputBase-input').should('not.be.disabled').click()
  })
  cy.wait(500)
  cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').eq(0).click()
  cy.contains('label', dropdown).parents('.MuiAutocomplete-root').first().find('.MuiInputBase-input').type('{esc}')
  cy.wait(300)
})

Then('The Activity items table returns values', () => {
  cy.get('[role="gridcell"][data-field="ACTIVITY_INSTANCE_NAME"]')
    .should(($cells) => {
      const hasValue = [...$cells].some((c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== '')
      expect(hasValue, 'Activity items table returned no values (empty) - possible bug').to.be.true
    })
})
