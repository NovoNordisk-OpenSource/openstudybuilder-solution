const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let criteriaName

When('User selects to create criteria from scratch', () => cy.get('[data-cy="criteria-from-scratch"] [type="radio"]').click())

When('User selects to create criteria from template', () => cy.get('[data-cy="criteria-from-template"] [type="radio"]').click())

When('User selects to create criteria from study', () => cy.get('[data-cy="criteria-from-study"] [type="radio"]').click())

When('User clicks add study criteria button', () => cy.clickButton('add-study-criteria'))

When('The {string} criteria from test study is copied', () => {
    cy.get('[data-cy="form-body"]').within(() => {
        cy.wait(3000)
        cy.clickFirstButton('Copy item')
        cy.get('.template-readonly').filter(':visible').first().invoke('text').then((val) => criteriaName = val)
    })
})

Then('The study criteria is searched and found', () => cy.searchAndCheckPresence(criteriaName, true))

When('The {string} criteria is copied from existing template', () => {
    cy.get('[data-cy="form-body"]').within(() => {
        cy.wait(1500)
        cy.contains('tbody > tr', 'testTemplate').filter(':visible').first().within(() => cy.clickButton('Select template'))
    })
})

Then('The {string} criteria created from existing template is visible within the table with correct data', (criteriaType) => {
    cy.wait(1000)
    cy.tableContains('testTemplate')
})

When('The {string} criteria is created from scratch', (value) => {
    criteriaName = `E2E ${value} criteria from scratch`
    cy.get('[data-placeholder="Criteria template"]').type(`E2E ${value} criteria from scratch`)
})
