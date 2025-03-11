const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let newVersion
let oidValue
let rowIndex
let itemGroupSelectedActivityGroup
let itemGroupDefaultName = Date.now()
let itemGroupDefaultOid = Date.now() + 5

When('The {string} action is clicked for the CRF Item Group', (action) => {
    cy.getValueFromCellsWithIndex(rowIndex, 1).then((oid) => oidValue = oid)
    cy.getValueFromCellsWithIndex(rowIndex, 7).then((curVersion) => newVersion = parseFloat(curVersion))
    cy.tableRowActions(rowIndex, action)
})

Given('The CRF Item Group in {string} status exists', (status) => {
    cy.getRowIndexByText(status).then(index => rowIndex = index)
})

Given('The CRF Item Group in draft status with sub 1 version exists', () => {
    cy.createCrfItemGroup('itemGroupForDelete')
    cy.getRowIndexByText('0.1').then(index => rowIndex = index)
})

Given('The CRF Item Group in {string} status and version {string} exists', (status, version) => {
    cy.getRowIndexByText(version).then(index => rowIndex = index)
})

When('The CRF Item Group definition container is filled with data and saved', () => {
    cy.fillInput('item-group-oid', itemGroupDefaultOid)
    cy.fillInput('item-group-name', itemGroupDefaultName)
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('save')
    cy.waitForTable()
})

Then("The newly added CRF Item Group is visible in the last row of the table", () => {
    cy.waitForTable()
    cy.tableContains(itemGroupDefaultOid)
    cy.tableContains(itemGroupDefaultName)
})

When('The CRF Item Group metadata are updated and saved', () => {
    cy.fillInput('item-group-oid', itemGroupDefaultOid + ' Edited')
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.fillInput('item-group-change-description', 'Test description')
    cy.clickFormActionButton('save')
    cy.waitForTable()
})

Then("The edited CRF Item Group is visible within the table", () => {
    cy.tableContains(' Edited')
})

Then('The CRF Item Group status is changed to {string} and version remain unchanged', (status) => {
    cy.wait(3000)
    cy.checkRowByIndex(rowIndex, 'Status', status)
})

Then('The CRF Item Group status is changed to {string} and version is incremented by {string}', (status, increment) => {
    cy.wait(3000)
    cy.checkRowByIndex(rowIndex, 'Status', status)
    cy.checkRowByIndex(rowIndex, 'Version', (newVersion + parseFloat(increment)).toFixed(1))
})

Then('The CRF Item Group status is changed to {string} and version is rounded up to full number', (status) => {
    cy.wait(3000)
    cy.checkRowByIndex(rowIndex, 'Status', status)
    cy.checkRowByIndex(rowIndex, 'Version', Math.ceil(newVersion))
})

Then('The CRF Item Group is no longer available', () => {
    cy.get('tbody').should('not.contain', oidValue)
})