const { Given, Then } = require("@badeball/cypress-cucumber-preprocessor");


Then('The current URL is {string}', (url) => {
    cy.url().should('contain', url)
})

Given('The {string} page is opened', (url) => {
    cy.visit(url)
    cy.waitForPage()
})

Given('The homepage is opened', () => {
    cy.visit('/')
})