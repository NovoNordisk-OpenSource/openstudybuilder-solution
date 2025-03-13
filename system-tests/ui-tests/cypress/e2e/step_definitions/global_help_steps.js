const {Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The Need Help? button is presented to the user with correct link to sharepoint site', () => {
    cy.get('[data-cy="topbar-need-help"]')
      .should("have.attr", "href")
      .should("not.be.empty")
      .and("contain", "https://openstudybuilder.com");
  })