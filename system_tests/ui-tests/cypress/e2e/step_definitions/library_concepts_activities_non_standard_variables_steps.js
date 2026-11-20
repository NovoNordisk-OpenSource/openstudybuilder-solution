const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let nsvCode, nsvLabel

When('User switches toggle on to allow mutilple selection of non-standard variable activity instace class', () => {
    cy.get('[data-cy="nsv-is-multiple"]').click()
})

When('User exapnds-collapse list of available activity instance classes', () => cy.get('[data-cy="nsv-activity-instance-class"]').click())

When('User selects {string} as one of non-standard activity instance classes', (value) => cy.contains('.v-list-item', value).click())

When('Non-standard variable activity instance class value is selected as {string}', (value) => {
    cy.selectVSelect('nsv-activity-instance-class', value)
})

When('Non-standard variable role is selected as {string}', (value) => cy.selectVSelect('nsv-role', value))

When('Non-standard variable data type is selected as {string}', (value) => cy.selectVSelect('nsv-data-type', value))

When('Non-standard variable code is set as random value', () => {
    cy.get('[data-cy="nsv-code"] input').clear().type(nsvCode = getShortUniqueId())
})

When('Non-standard variable code is set with already used value', () => {
    cy.get('[data-cy="nsv-code"] input').clear().type(nsvCode)
})

When('Non-standard variable label is set as {string}', (value) => {
    cy.get('[data-cy="nsv-label"] input').clear().type(nsvLabel = `${value} ${getShortUniqueId()}`)
})

When('Non-standard variable length is set as {string}', (value) => {
    cy.get('[data-cy="nsv-length"] input').clear().type(value)
})

When('Non-standard variable optional input field {string} is set to {string}', (name, value) => {
    cy.contains('.v-overlay .v-input', name).find('input, textarea').not('.v-textarea__sizer').clear().type(value)
})

When('Non-standard variable optional dropdown field {string} is set to {string}', (name, value) => {
    cy.contains('.v-overlay .v-input', name).find('.v-field').click()
    cy.contains('.v-list-item', value).click()
})

When('Non-standard variable activity instane class is cleared', () => cy.get('[aria-label^="Clear Activity Instance Class"]').click())

When('Non-standard variable role is cleared', () => cy.get('[aria-label^="Clear Role"]').click())

Then('Non-standard variable is searched by code and found', () => cy.searchAndCheckPresence(nsvCode.toUpperCase(), true))

Then('Non-standard variable is searched by code and not found', () => cy.searchAndCheckPresence(nsvCode.toUpperCase(), false))

Then('Warning is displayed that the non-standad variable code is already used', () => {
    cy.checkSnackbarMessage(`Non Standard Variable with Code '${nsvCode.toUpperCase()}' already exists.`)
})

Then('Warning is displayed that filed {string} is required for non-standard variable', (name) => {
    cy.get(`[data-cy="nsv-${name}"]`).should('contain.text', 'This field is required')
})

Then('Non-standard variable {string} is visible as {string} in the table', (name, value) => cy.checkRowByIndex(0, name, value))

Then('Non-standard variable code, label and name are visible in the table with correct values', () => {
    cy.checkRowByIndex(0, 'NSV code', nsvCode.toUpperCase())
    cy.checkRowByIndex(0, 'NSV label', nsvLabel)
    cy.checkRowByIndex(0, 'Name', nsvLabel.replaceAll(' ', '_').toLowerCase())
})

When('User goes to non-standard variable overview page by clicking its name', () => {
    cy.get('table tbody tr td').contains(nsvLabel.replaceAll(' ', '_').toLowerCase()).click()
})

When('Non-standard variable sentence case name has correct value in the overview page', () => {
    cy.contains('.activity-summary-table tbody td', 'Sentence case name').should('contain.text', nsvLabel.replaceAll(' ', '_').toLowerCase())
})

When('Non-standard variable label has correct value in the overview page', () => {
    cy.contains('.activity-summary-table tbody td', 'Label').should('contain.text', nsvLabel)
})

When('Non-standard variable {string} has value {string} in the overview page', (name, value) => {
    cy.contains('.activity-summary-table tbody td', name).should('contain.text', value)
})

When('Non-standard variable is connected to Activity Instance Class {string}', (value) => {
    cy.contains('.activity-section table tbody tr', value).should('be.visible')
})
