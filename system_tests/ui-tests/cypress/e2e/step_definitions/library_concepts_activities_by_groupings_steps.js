const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");


Then('User expands activity groupings for group {string} and subgroup {string}', (group, subgroup) => {
    cy.contains('table tbody tr[style*="BackgroundLight1"]', group).find('button .mdi-chevron-right').click()
    cy.contains('table tbody tr[style*="BackgroundLight2"]', subgroup).find('button .mdi-chevron-right').click()
})

Then('User sees linked activity {string} in the activities by grouping table', (activity) => {
    cy.contains('table tbody table tbody table tbody tr', activity).should('be.visible')
})