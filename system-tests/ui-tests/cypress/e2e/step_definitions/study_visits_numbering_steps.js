const { Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The first visit within the group is visible with Visit Number 1 and Unique Number 100', () => {
    cy.checkRowByIndex(0, 'Visit number', 1)
    cy.checkRowByIndex(0, 'Unique visit number', 1)
})

Then('Each visit within the group has the Visit Number and Unique number incremented by 1 and 100 respectfully', () => {
    cy.checkRowByIndex(0, 'Visit number', 1)
    cy.checkRowByIndex(0, 'Unique visit number', 100)
    cy.checkRowByIndex(1, 'Visit number', 2)
    cy.checkRowByIndex(1, 'Unique visit number', 200)
    cy.checkRowByIndex(2, 'Visit number', 3)
    cy.checkRowByIndex(2, 'Unique visit number', 300)
    cy.checkRowByIndex(3, 'Visit number', 4)
    cy.checkRowByIndex(3, 'Unique visit number', 400)
    cy.checkRowByIndex(4, 'Visit number', 5)
    cy.checkRowByIndex(4, 'Unique visit number', 500)
})