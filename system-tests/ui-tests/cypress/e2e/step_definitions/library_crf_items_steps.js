const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let newVersion
let oidValue
let elementIndex
let itemSelectedActivityGroup
let crfItemOidDefault = Date.now()
let crfItemNameDefault = Date.now() + 5

When('The Delete action is clicked for the CRF Item', () => {
    cy.rowActionsByValue(oidValue, 'Delete')
})

When('The {string} action is clicked for the CRF Item', (action) => {
    cy.getValueFromCellsWithIndex(elementIndex, 9).then((curVersion) => newVersion = parseFloat(curVersion))
    cy.tableRowActions(elementIndex, action)
})

Given('The CRF Item in {string} status exists', (status) => {
    cy.getRowIndexByText(status).then(rowIndex => elementIndex = rowIndex)
})

Given('The CRF Item in draft status with sub 1 version exists', () => {
    oidValue = 'oidForDelete'
    cy.createCrfItem(oidValue)
    cy.getRowIndexByText(oidValue).then(rowIndex => elementIndex = rowIndex)
})

Given('The CRF Item with linked Activity exists', () => {
    cy.getRowIndexByText(itemSelectedActivityGroup).then(rowIndex => elementIndex = rowIndex)
})

When('The CRF Item definition container is filled with data and saved', () => {
    cy.fixture('crfItem.js').then((item) => {
        cy.fillInput('item-oid', crfItemOidDefault)
        cy.fillInput('item-name', crfItemNameDefault)
        cy.selectVSelect('item-data-type', item.details.data_type)
        cy.clickFormActionButton('continue')
        cy.clickFormActionButton('continue')
        cy.clickFormActionButton('continue')
        cy.clickFormActionButton('save')
        cy.waitForTable()
    })
})

Then("The newly added CRF Item is visible in the last row of the table", () => {
    cy.fixture('crfItem.js').then(() => {
        cy.waitForTable()
        cy.get('.v-data-table-footer .mdi-page-last').click({ force: true })
        cy.waitForTable()
        cy.checkLastRow('OID',crfItemOidDefault)
        cy.checkLastRow('Name',crfItemNameDefault)
    })
})

When('The CRF Item metadata are updated and saved', () => {
    cy.fixture('crfItem.js').then((item) => {
        cy.fillInput('item-name', crfItemNameDefault + ' Edited')
        cy.clickFormActionButton('continue')
        cy.clickFormActionButton('continue')
        cy.clickFormActionButton('continue')
        cy.clickFormActionButton('continue')
        cy.fillInput('item-change-description', 'Test Change Description')
        cy.clickFormActionButton('save')
        cy.waitForTable()
    })
})

Then("The edited CRF Item is visible within the table", () => {
    cy.fixture('crfItem.js').then((item) => {
        cy.wait(1000)
        cy.tableContains(crfItemNameDefault + ' Edited')
    })
})

Then('The CRF Item status is changed to {string} and version remain unchanged', (status) => {
    cy.checkRowByIndex(elementIndex, 'Status', status)
})

Then('The CRF Item status is changed to {string} and version is incremented by {string}', (status, increment) => {
    cy.waitForTable()
    cy.checkRowByIndex(elementIndex, 'Status', status)
    cy.checkRowByIndex(elementIndex, 'Version', (newVersion + parseFloat(increment)).toFixed(1))
})

Then('The CRF Item status is changed to {string} and version is rounded up to full number', (status) => {
    cy.wait(3000)
    cy.checkRowByIndex(elementIndex, 'Status', status)
    cy.checkRowByIndex(elementIndex, 'Version', Math.ceil(newVersion))
})

Then('The CRF Item is no longer available', () => {
    cy.wait(4000)
    cy.contains(oidValue).should('not.exist')
})
