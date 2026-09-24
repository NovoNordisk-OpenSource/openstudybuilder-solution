import { getCurrStudyUid, getShortUniqueId } from "../../support/helper_functions";

const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

export let selectedSupplierValue
let selectedSupplierValues = []

When('User intercepts data supplier request', () => cy.intercept('/api/studies/*/study-data-suppliers?*').as('dataSuppliers'))

When('User waits for data supplier request', () => cy.wait('@dataSuppliers'))

When('Data supplier type {string} is searched and found', (type) => cy.searchAndCheckPresence(type, true))

When('Data supplier is searched and found', () => cy.searchAndCheckPresence(selectedSupplierValue, true))

When('User defined data supplier is searched and not found', () => cy.searchAndCheckPresence(selectedSupplierValue, false))

When('User clicks ADD USER DEFINED DATA SUPPLIER button', () => cy.contains('button', 'Add user defined data supplier').click())

Then('The Edit Study Data Supplier page is opened', () => cy.contains('.page-title', 'Edit Study Data Supplier').should('be.visible'))

When('User initiate adding value for data supplier type {string}', (type) => {
    cy.contains('.supplier-type-section', type).find('button .mdi-plus').click()
    cy.contains('.supplier-type-section', type).find('.v-select input[role="combobox"][value=""]').parent().click()
})

When('User clicks remove button for previously selected value for data supplier type {string}', (type) => {
    cy.contains('.supplier-type-section', type).contains('.mb-3', selectedSupplierValue).contains('button', 'Remove').click()
})

When('[API] All data suppliers are removed from selected study', () => cy.deleteDataSuppliersFromStudy(getCurrStudyUid()))

When('User finds one of the user defined values for data supplier', () => {
    cy.contains('.v-overlay__content .v-list-item', 'DS_').invoke('text').then(text => selectedSupplierValue = text)
})

When('User saves first available value of data supplier type {string}', (type) => {
    cy.contains('.supplier-type-section', type).get('.mb-3 .v-field[role="combobox"]').eq(0).invoke('text').then(text => selectedSupplierValue = text)
})

When('User saves data supplier value with index {int}', (index) => {
    cy.get('.v-overlay__content .v-list-item').eq(index).invoke('text').then(text => (selectedSupplierValue = text, selectedSupplierValues.push(text)))
})

When('User selects data supplier value from previous step', () => cy.contains('.v-overlay__content .v-list-item', selectedSupplierValue).click());

Then('The selected value is visible in the dropdown for data supplier type {string}', (type) => {
    cy.contains('.supplier-type-section', type).find('.v-select').first().find('.v-field[role="combobox"]').should('have.text', selectedSupplierValue)
})

Then('The newly added value should be displayed in the table with for data supplier type {string}', (type) => checkTableValues(0, type, selectedSupplierValue))

Then('Both values are searched and correct data is displayed in the table for data supplier type {string}', (type) => {
    selectedSupplierValues.forEach(val => (cy.searchAndCheckPresence(val, true), checkTableValues(0, type, val)))
})

Then('The value is removed from the data supplier type {string}', (type) => {
    cy.contains('.supplier-type-section', type).contains('.v-input', selectedSupplierValue).should('not.exist')
})

Then('The value is removed from the overview for data supplier type {string}', (type) => {
    cy.contains('.supplier-type-section', type).contains('.mb-3', selectedSupplierValue).should('not.exist')
})

Then('Both values are displayed on the overview page for data supplier type {string}', (type) => selectedSupplierValues.forEach(val => checkIfSupplierValueAvailable(type, val)))

Then('The newly added value should be visible for data supplier type {string}', (type) => checkIfSupplierValueAvailable(type, selectedSupplierValue))

Then('The Add User Defined Data Supplier form is opened', () => cy.contains('.dialog-title', 'Add a new Data Supplier').should('be.visible'))

When('User fills in data supplier name', () => cy.get('[data-cy="data-supplier-name"] input').type(selectedSupplierValue = `DS_${getShortUniqueId()}`))

function checkIfSupplierValueAvailable(dataSupplierType, expectedValue) {
    cy.contains('.supplier-type-section', dataSupplierType).contains('.mb-3', expectedValue).should('be.visible')
}

function checkTableValues(rowIndex, expectedType, expectedValue) {
    cy.checkRowByIndex(rowIndex, 'Study Data Supplier Type', expectedType)
    cy.checkRowByIndex(rowIndex, 'Data supplier name', expectedValue)
}