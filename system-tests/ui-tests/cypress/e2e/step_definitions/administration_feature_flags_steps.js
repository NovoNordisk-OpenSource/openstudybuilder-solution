const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Given("The toggle is set to on", () => toggleOnOff(true));

Given("The toggle is set to off", () => toggleOnOff(false));

When("Click the View Listings side-menu", () => cy.get('.v-list-item-title').contains('View Listings').click())

Then("The sub-menu Analysis Study Metadata should exist", () => checkIfItemAvailableInMenu('Analysis Study Metadata (New)', true))

Then("The sub-menu Analysis Study Metadata should not exist", () => checkIfItemAvailableInMenu('Analysis Study Metadata (New)', false))

function toggleOnOff(on) {
    cy.wait(1000)
    on ? cy.get('table .v-switch input').check() : cy.get('table .v-switch input').uncheck()
  }

function checkIfItemAvailableInMenu(name, shouldExists) {
  const condition = shouldExists ? 'be.visible' : 'not.exist'
  cy.get(`[data-cy="${name}"]`).should(condition);
}
