const { Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The visists naming is derived from Visit + order of visit in group', () => {
    cy.tableContains('Visit 1')
    cy.tableContains('Visit 2')
    cy.tableContains('Visit 3')
    cy.tableContains('Visit 4')
    cy.tableContains('Visit 5')
    cy.tableContains('Visit 6')
})

Then('The visists naming is derived from V + order of visit in group', () => {
    cy.tableContains('V1')
    cy.tableContains('V2')
    cy.tableContains('V3')
    cy.tableContains('V4')
    cy.tableContains('V5')
    cy.tableContains('V6')
})

// Then('The visists naming is derived from P + order of visit in group', () => {
//     cy.tableContains('Visit 1')
//     cy.tableContains('Visit 2')
//     cy.tableContains('Visit 3')
//     cy.tableContains('Visit 4')
//     cy.tableContains('Visit 5')
//     cy.tableContains('Visit 6')
// })

// Then('The visists naming is derived from O + order of visit in group', () => {
//     cy.tableContains('Visit 1')
//     cy.tableContains('Visit 2')
//     cy.tableContains('Visit 3')
//     cy.tableContains('Visit 4')
//     cy.tableContains('Visit 5')
//     cy.tableContains('Visit 6')
// })

Then('The visists naming is derived from Day + amount of days in relation to visit time reference', () => {
    cy.tableContains('Day -14')
    cy.tableContains('Day 1')
    cy.tableContains('Day 8')
    cy.tableContains('Day 15')
    cy.tableContains('Day 22')
    cy.tableContains('Day 29')
})
Then('The visists naming is derived from Week + amount of days in relation to visit time reference', () => {
    cy.tableContains('Week -2')
    cy.tableContains('Week 1')
    cy.tableContains('Week 2')
    cy.tableContains('Week 3')
    cy.tableContains('Week 4')
    cy.tableContains('Week 5')
})