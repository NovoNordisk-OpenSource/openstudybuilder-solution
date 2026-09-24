const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");


When('Study {string} is searched and found', (name) => cy.searchAndCheckPresence(name, true))

When('Study {string} is searched and not found', (name) => cy.searchAndCheckPresence(name, false))

When('Study is selected as a template', () => cy.get('button[title="Select study"]').click())

When('Study is deselected as a template', () => cy.contains('button', 'Reset template').click())
