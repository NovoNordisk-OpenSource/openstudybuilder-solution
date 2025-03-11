const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let newVersion
let rowIndex
let oidValue
let templateOidDefault = Date.now()
let templateNameDefault = Date.now() + 5

Given('The CRF Template in {string} status exists', (status) => {
    cy.getRowIndexByText(status).then(index => rowIndex = index)
})

Given('The CRF Template in draft status with sub 1 version exists', () => {
    cy.createCrfTemplate()
    cy.getRowIndexByText('0.1').then(index => rowIndex = index)
})

Given('The CRF Template in {string} status and version {string} exists', (status, version) => {
    cy.getRowIndexByText(version).then(index => rowIndex = index)
})

When('The {string} action is clicked for the CRF Template', (action) => {
    cy.getValueFromCellsWithIndex(rowIndex, 1).then((oid) => oidValue = oid)
    cy.getValueFromCellsWithIndex(rowIndex, 5).then((curVersion) => newVersion = parseFloat(curVersion))
    cy.tableRowActions(rowIndex, action)
})

When('The CRF Template definition container is filled with data and saved', () => {
    cy.fixture('crfTemplate.js').then((template) => {
        cy.fillInput('crf-template-oid', templateOidDefault)
        cy.fillInput('crf-template-name', templateNameDefault)
        cy.selectDatePicker('crf-template-effective-date', template.effective_date)
        cy.selectDatePicker('crf-template-retired-date', template.retired_date)
        cy.clickButton('save-button')
        cy.waitForFormSave()
        cy.checkSnackbarMessage('Template created')
    })
})

Then('The newly added CRF Template is visible in the last row of the table', () => {
    cy.fixture('crfTemplate.js').then((template) => {
        cy.tableContains(templateOidDefault)
        cy.tableContains(templateNameDefault)
        cy.tableContains(template.effective_date)
        cy.tableContains(template.retired_date)
        cy.tableContains('Draft')
    })
})

When('The CRF Template definition container is filled without name provided', () => {
    cy.wait(100)
})

Then('The validation appears for the CRF Template Name field', () => {
    cy.get('.v-messages__message').should('be.visible')
})

When('The CRF Template metadata are updated and saved', () => {
    cy.fixture('crfTemplate.js').then((template) => {
        cy.fillInput('crf-template-oid', templateOidDefault + ' Edited')
        cy.fillInput('crf-template-name', templateNameDefault + ' Edited')
        cy.selectDatePicker('crf-template-effective-date', template.effective_date + 1)
        cy.selectDatePicker('crf-template-retired-date', template.retired_date + 1)
        cy.clickButton('save-button')
        cy.waitForFormSave()
        cy.checkSnackbarMessage('Template updated')
    })
})

Then('The edited CRF Template is visible within the table', () => {
    cy.fixture('crfTemplate.js').then((template) => {
        cy.waitForTable()
        cy.tableContains(templateOidDefault + ' Edited')
        cy.tableContains(templateNameDefault + ' Edited')
        cy.tableContains(template.effective_date + 1)
        cy.tableContains(template.retired_date + 1)
        cy.tableContains('Draft')
    })
})

Then('The CRF Template status is changed to {string} and version remain unchanged', (status) => {
    cy.wait(3000)
    cy.checkRowByIndex(rowIndex, 'Status', status)
})

Then('The CRF Template status is changed to {string} and version is incremented by {string}', (status, increment) => {
    cy.wait(3000)
    cy.checkRowByIndex(rowIndex, 'Status', status)
    cy.checkRowByIndex(rowIndex, 'Version', (newVersion + parseFloat(increment)).toFixed(1))
})

Then('The CRF Template status is changed to {string} and version is rounded up to full number', (status) => {
    cy.wait(3000)
    cy.checkRowByIndex(rowIndex, 'Status', status)
    cy.checkRowByIndex(rowIndex, 'Version', Math.ceil(newVersion))
})

Then('The CRF Template is no longer available', () => {
    cy.wait(3000)
    cy.tableNotContains(oidValue)
})