const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Given("The toggle is set to on", () => toggleAllOnOff(true));

Given("The toggle is set to off", () => toggleAllOnOff(false));

When("Click the View Listings side-menu", () => cy.get('.v-list-item-title').contains('View Listings').click())

Then("The sub-menu Analysis Study Metadata should exist", () => checkIfItemAvailableInMenu('Analysis Study Metadata (New)', true))

Then("The sub-menu Analysis Study Metadata should not exist", () => checkIfItemAvailableInMenu('Analysis Study Metadata (New)', false))

When('Activity instance wizard feature flag is turned off', () => toggleOnOff('create/edit Activity Instances', false))

When('Activity instance wizard feature flag is turned on', () => toggleOnOff('create/edit Activity Instances', true))

function toggleAllOnOff(on) {
  cy.wait(1000)
  on ? cy.get('table .v-switch input').check() : cy.get('table .v-switch input').uncheck()
}

function checkIfItemAvailableInMenu(name, shouldExists) {
  const condition = shouldExists ? 'be.visible' : 'not.exist'
  cy.get(`[data-cy="${name}"]`).should(condition);
}

function toggleOnOff(featureName, on) {
  cy.contains('table tbody tr', featureName).find('.v-switch input').then(el => on ? cy.wrap(el).check() : cy.wrap(el).uncheck())
}
