const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('User expands view to see linked instance class for {string}', (parentInstanceClass) => {
    cy.contains('table tbody tr', parentInstanceClass).find('button .mdi-chevron-right').click()
})

Then('Activity Instance class {string} is visible in the table', (instanceClassName) => {
    cy.contains('table tbody tr', instanceClassName).should('be.visible')
})
