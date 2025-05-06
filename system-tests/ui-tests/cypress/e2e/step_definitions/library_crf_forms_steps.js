const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let newVersion
let oidValue
let rowIndex
let formSelectedActivityGroup
let formNameDefault = Date.now()
let formOidDefault = Date.now()

When('The {string} action is clicked for the CRF Form', (action) => {
    cy.getValueFromCellsWithIndex(rowIndex, 1).then((oid) => oidValue = oid)
    cy.getValueFromCellsWithIndex(rowIndex, 7).then((curVersion) => newVersion = parseFloat(curVersion))
    cy.tableRowActions(rowIndex, action)
})

Given('The CRF Form in {string} status exists', (status) => {
    cy.getRowIndexByText(status).then(index => rowIndex = index)
})

Given('The CRF Form in {string} status and version {string} exists', (status, version) => {
    cy.getRowIndexByText(version).then(index => rowIndex = index)
})

Given('The CRF Form with linked Activity Group exists', () => {
    cy.getRowIndexByText(formSelectedActivityGroup).then(index => rowIndex = index)
})

Given('The CRF Form in draft status with sub 1 version exists', () => {
    oidValue = 'formForDelete'
    cy.createCrfForm(oidValue)
    cy.searchFor(oidValue)
})

When('The Form definition container is filled with data and saved', () => {
    cy.fillInput('form-oid', formOidDefault)
    cy.fillInput('form-oid-name', formNameDefault)
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('save')
    cy.waitForTable()
})

Then("The newly added form is visible in the last row of the table", () => {
    cy.fillInput('search-field', formNameDefault)
    cy.tableContains(formNameDefault)
})

When('The Form metadata are updated and saved', () => {
    cy.fillInput('form-oid', formOidDefault + ' Edited')
    cy.fillInput('form-oid-name', formNameDefault + ' Edited')
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.fillInput('form-change-description', 'Change description for edit scenario')
    cy.clickFormActionButton('save')
    cy.waitForTable()
    cy.checkSnackbarMessage('Form updated')
})

Then("The edited CRF Form is visible within the table", () => {
    cy.tableContains(formNameDefault + ' Edited')
})

Then('The Form status is changed to {string} and version remain unchanged', (status) => {
    cy.wait(3000)
    cy.checkRowByIndex(rowIndex, 'Status', status)
})

Then('The Form status is changed to {string} and version is incremented by {string}', (status, increment) => {
    cy.wait(3000)
    cy.checkRowByIndex(rowIndex, 'Status', status)
    cy.checkRowByIndex(rowIndex, 'Version', (newVersion + parseFloat(increment)).toFixed(1))
})

Then('The Form status is changed to {string} and version is rounded up to full number', (status) => {
    cy.wait(3000)
    cy.checkRowByIndex(rowIndex, 'Status', status)
    cy.checkRowByIndex(rowIndex, 'Version', Math.ceil(newVersion))
})

Then('The CRF Form is no longer available', () => cy.confirmItemNotAvailable(oidValue))