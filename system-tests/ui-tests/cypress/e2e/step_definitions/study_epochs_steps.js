const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let epochIndex
let epochDescription = `Epoch ${Date.now()}`
let epochEditedDescription = `Edited epoch ${Date.now()}`

When('A new Study Epoch is added', () => {
    cy.waitForData('study-epochs')
    cy.clickButton('create-epoch')
    cy.selectAutoComplete('epoch-type', 'Post Treatment')
    cy.selectAutoComplete('epoch-subtype', 'Elimination')
    cy.fillInput('description', epochDescription)
    cy.fillInput('epoch-start-rule', 'D10')
    cy.fillInput('epoch-end-rule', 'D99')
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

Then('The new Study Epoch is available within the table', () => {
    cy.waitForData('study-epochs')
    cy.checkLastRow('Epoch name', 'Elimination')
    cy.checkLastRow('Epoch type', 'Post Treatment')
    cy.checkLastRow('Epoch subtype', 'Elimination')
    cy.checkLastRow('Start rule', 'D10')
    cy.checkLastRow('End rule', 'D99')
    cy.checkLastRow('Description', epochDescription)
})

Given('The Study Epoch exists in the Study', () => {
    cy.waitForTableData()
    cy.get('[data-cy="table-item-action-button"]').first().parentsUntil('tr').invoke('index').then((epoch) => {
        epochIndex = epoch
    })
})

When('The Study Epoch is edited', () => {
    cy.tableRowActions(epochIndex, 'Edit')
    cy.wait(1000)
    cy.fillInput('epoch-start-rule', 'D22')
    cy.fillInput('epoch-end-rule', 'D33')
    cy.fillInput('description', epochEditedDescription)
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

When('The Epoch edit form is opened', () => {
    cy.tableRowActions(epochIndex, 'Edit')
})

Then('The Type and Subtype fields are disabled', () => {
    cy.checkIfInputDisabled('epoch-type')
    cy.checkIfInputDisabled('epoch-subtype')
})

Then('The edited Study Epoch with updated values is available within the table', () => {
    cy.checkRowByIndex(epochIndex, 'Description', epochEditedDescription)
    cy.checkRowByIndex(epochIndex, 'Start rule', 'D22')
    cy.checkRowByIndex(epochIndex, 'End rule', 'D33')
})

When('The Study Epoch is deleted', () => {
    cy.waitForTableData()
    cy.getCellValue(epochIndex, 'Description').as('deletedEpoch')
    cy.get('@deletedEpoch').then((epoch) => { cy.log(epoch) })
    cy.tableRowActions(epochIndex, 'Delete')
})

Then('The Epoch is not visible in the table', () => {
    cy.waitForTableData()
    cy.get('@deletedEpoch').then((epoch) => {
        cy.get('tbody').should('not.contain', epoch)
    })
})