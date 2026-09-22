// Import commands.js using ES2015 syntax:
import '@shelex/cypress-allure-plugin'
import './helper_functions'
import './auth'
import './table_commands'
import './input_field_commands'

Cypress.on('uncaught:exception', (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false
})

//Run that command once prior to the whole test suit
before(function() {
    cy.prepareAuthTokens()
});