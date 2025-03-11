const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The identifiers are set with following data', (dataTable) => {
    //null on all
    cy.nullRegistryIdentifiersForStudy()
    cy.waitForTable()
    cy.clickButton('edit-content')
    dataTable.hashes().forEach((element) => {
        cy.fillInput(element.identifier, element.value)
    })
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

When('The not applicable is checked for all identifiers', (dataTable) => {
    //null on all
    cy.nullRegistryIdentifiersForStudy()
    cy.waitForTable()
    cy.clickButton('edit-content')
    cy.checkAllCheckboxes()
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

Then('The identifiers table is showing following data', (dataTable) => {
    cy.waitForTableData()
    dataTable.hashes().forEach((element) => {
        cy.tableContains(element.value)
    })
})

