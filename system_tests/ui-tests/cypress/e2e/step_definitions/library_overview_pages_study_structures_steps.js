const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('User intercepts study structures requests', () => cy.intercept('/api/studies/structure-overview?*').as('getData'))

When('User waits for study structures requests', () => cy.wait('@getData', {timeout: 60000}))
