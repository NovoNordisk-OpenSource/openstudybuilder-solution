const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Given('The user is logged in', () => {
  if (Cypress.env('NEODASH_USERNAME') == "") {
    cy.visit('/')
  } else {
    let user = Cypress.env('NEODASH_USERNAME')
    let id_token = Cypress.env('NEODASH_ACCESS_TOKEN')
    cy.visit('/')
    cy.get('.ndl-form-item-label > input').click()
    cy.get('#dbusername').clear().type(user)
    cy.get('#dbpassword').type(id_token, { delay: 0})
    cy.wait(500)
    cy.get('button').contains('Connect').click()
  }
});