const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let criteriaName

When('The {string} criteria is created from studies', () => {
    cy.clickButton('add-study-criteria')
    cy.get('[data-cy="criteria-from-study"]').within(() => {cy.get('[type="radio"]').click() })
    cy.clickFormActionButton('continue')
})

When('The test study for {string} criteria copying is selected by study id', () => {
    cy.selectFirstVSelect('Select studies')
    cy.clickFormActionButton('continue')
})

When('The {string} criteria from test study is copied', () => {
    cy.get('[data-cy="form-body"]').within(() => {
        cy.wait(3000)
        cy.clickFirstButton('Copy item')
        cy.get('.template-readonly').filter(':visible').first().invoke('text').then((val) => {
            criteriaName = val
        })
        cy.clickFormActionButton('save')
    })
    cy.waitForTable()
})

Then('The {string} copied from test study is visible within the table with correct data', () => {
    cy.wait(2000)
    cy.tableContains(criteriaName)
})

When('The {string} criteria is copied from existing template', (criteriaType) => {
    cy.createCriteriaTemplate(criteriaType)
    cy.wait(1500)
    cy.clickButton('add-study-criteria')
    cy.get('[data-cy="criteria-from-template"]').within(() => {cy.get('[type="radio"]').click() })
    cy.clickFormActionButton('continue')
    cy.get('[data-cy="form-body"]').within(() => {
        cy.wait(1500)
        cy.contains('tbody > tr', 'testTemplate')
            .filter(':visible')
            .first()
            .within(() => {
                cy.clickButton('Select template', true)
            })
        cy.clickFormActionButton('save')
    })
})

Then('The {string} criteria created from existing template is visible within the table with correct data', (criteriaType) => {
    cy.wait(1000)
    cy.tableContains('testTemplate')
})

When('The {string} criteria is created from scratch', (string) => {
    cy.clickButton('add-study-criteria')
    cy.get('[data-cy="criteria-from-scratch"]').within(() => {cy.get('[type="radio"]').click() })
    cy.clickFormActionButton('continue')
    cy.get('[data-placeholder="Criteria template"]').type('Test ' + string + ' criteria from scratch')
    cy.wait(1000)
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('save')
})

Then('The {string} criteria created from new template is visible within the table with correct data', (string, docstring) => {
    cy.wait(1000)
    cy.tableContains('Test ' + string + ' criteria from scratch')
})