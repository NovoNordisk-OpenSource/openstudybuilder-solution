const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('Activity Item class is searched for and found', () => cy.searchAndCheckPresence('date_of_birth', true))

Then('Activity Item class is searched for by partial name', () => cy.searchFor('date'))