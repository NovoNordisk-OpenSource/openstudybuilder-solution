const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let data_supplier_name, description, apiBaseUrl, uiBaseUrl, defaultSupplierType, originSource, originType

Given('The data supplier is found', () => cy.searchAndCheckPresence(data_supplier_name, true))

Given('The user defines data supplier name, type, description, order, api url, frontend url, origin source and origin type', () => {
    data_supplier_name = `E2E ${getShortUniqueId()}`
    description = 'Test Description', apiBaseUrl = 'APIURL', uiBaseUrl = 'UIURL'
    defaultSupplierType = 'EDC System', originSource = 'Clinical Study Sponsor', originType = 'Assigned Value'
    fillDataSupplierData()
})

When('The user edits data supplier name, type, description, order, api url, frontend url, origin source and origin type', () => {
    data_supplier_name = `Update ${data_supplier_name}`
    description += 'Update', apiBaseUrl += '1', uiBaseUrl += '1'
    defaultSupplierType = 'Lab Data Exchange Files', originSource = 'Investigator', originType = 'Collected Value'
    fillDataSupplierData()
})

Then('The data supplier data is visible in the table', () => {
    cy.checkRowByIndex(0, 'Name', data_supplier_name)
    cy.checkRowByIndex(0, 'Order', '2')
    cy.checkRowByIndex(0, 'Description', description)
    cy.checkRowByIndex(0, 'API base URL', apiBaseUrl)
    cy.checkRowByIndex(0, 'UI base URL', uiBaseUrl)
    cy.checkRowByIndex(0, 'Default Supplier Type', defaultSupplierType)
    cy.checkRowByIndex(0, 'Origin Source', originSource)
    cy.checkRowByIndex(0, 'Origin Type', originType)
})

When('The user intercepts version history request', () => cy.intercept('**versions').as('versionHistory'))

Then('The changes history is presented to the user', () => {
    cy.wait('@versionHistory').then(req => {
        cy.get('[data-cy="version-history-window"]').within(() => {
            req.response.body.forEach((item, index) => {
                cy.checkRowByIndex(index, 'Name', item.name)
                cy.checkRowByIndex(index, 'Order', item.order)
                cy.checkRowByIndex(index, 'Version', item.version)
            })
        })
    })
})

function fillDataSupplierData() {
    cy.fillInput('data-supplier-name', data_supplier_name)
    cy.selectVSelect('data-supplier-type-uid', defaultSupplierType)
    cy.fillInput('data-supplier-order', '2')
    cy.get('[data-cy="data-supplier-description"]').eq(0).type(description)
    cy.get('[data-cy="data-supplier-description"]').eq(1).type(apiBaseUrl)
    cy.get('[data-cy="data-supplier-description"]').eq(2).type(uiBaseUrl)
    cy.selectVSelect('data-supplier-origin-source-uid', originSource)
    cy.selectVSelect('data-supplier-origin-type-uid', originType)
}