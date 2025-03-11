const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
let compoundType

Given('The study compound is available in the test study', () => {
    cy.testCompound()
})

When('The study compound is added', () => {
    cy.clickButton('add-study-compound')
    cy.fixture('studyCompound').then((compound) => {
        compoundType = compound.type_of_treatment
        cy.selectAutoComplete('Type of treatment', compoundType)
        cy.clickButton('type_of_treatment-continue-button')
        cy.contains('.v-select__slot', 'Compound').click({ force: true })
        cy.get('.v-menu__content')
            .filter(':visible')
            .should('not.contain', 'No data available')
        cy.get('.v-menu__content')
            .filter(':visible')
            .within(() => {
                cy.contains('.v-list-item', compound.compound).click()
            })
        cy.get('[data-cy="form-body"]').click({ force: true })
        cy.contains('.v-select__slot', 'Compound alias').click({ force: true })
        cy.get('.v-menu__content')
            .filter(':visible')
            .should('not.contain', 'No data available')
        cy.get('.v-menu__content')
            .filter(':visible')
            .within(() => {
                cy.contains('.v-list-item', compound.compound).click()
            })
        cy.get('[data-cy="form-body"]').click({ force: true })
        cy.clickButton('compoundAlias-continue-button')
        cy.clickButton('compound-save-button')
    })
})

Then('The study compound is available in the table', () => {
    cy.waitForTableData()
    cy.tableContains(compoundType)
})

When('The study compound is edited', () => {
    cy.waitForTableData()
    cy.tableRowActions(0, 'Edit')
    cy.fixture('studyCompound').then((compound) => {
        cy.selectAutoComplete('Type of treatment', compound.edit_typeof_treatment)
        cy.clickButton('type_of_treatment-continue-button')
        cy.clickButton('compoundAlias-continue-button')
        cy.clickButton('compound-save-button')
    })
})

Then('The updated study compound is available in the table', () => {
    cy.fixture('studyCompound').then((compound) => {
        cy.waitForTableData()
        cy.tableContains(compound.edit_typeof_treatment)
    })
})

When('The study compound is deleted', () => {
    cy.waitForTableData()
    cy.tableRowActions(0, 'Delete')
    cy.contains('.v-btn__content', 'Continue').click({ force: true })
    cy.checkSnackbarMessage('Study compound deleted')
})

Then('The study compound is no longer available', () => {
    cy.waitForTableData()
    cy.get('tbody').should('not.contain', compoundType)
})