import { element_uid } from "../../support/api_requests/study_elements_requests";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid } = require("../../support/helper_functions");

let transitionRule
const fillTransitionRule = (value) => cy.get('.v-card textarea').clear().type(transitionRule = value, {delay: 0})

When('User saves changes made in the edition mode', () => cy.get('button[title="Save"]').click())

When('Transion rules are enabled', () => cy.get('input[title="Enable transition rules mode"]').check())

When('Transion rules are disabled', () => cy.get('input[title="Enable transition rules mode"]').uncheck())

When('Transition rules edit window is opened', () => cy.get('.v-overlay .v-card-title').should('have.text', 'Transition Rule'))

When('{int} element is selected', (elementIndex) => cy.get('.v-select__content .v-list-item').eq(elementIndex).click())

Then('User triggers dropdown for element assignment to epoch {string}', (epochName) => perfomAction(epochName, '[role="combobox"] .v-field__input'))

Then('User triggers dropdown for element assignment to epoch {string}, branch {string}', (epochName, branchName) => perfomActionForSpecificBranch(epochName, branchName, '[role="combobox"] .v-field__input'))

Then('User open transition rules edit mode for epoch {string}', (epochName) => perfomAction(epochName, 'button[hide-details]'))

Then('User sets transition rule', () => fillTransitionRule('Transition Rule 1'))

Then('Transition rule is visible in the table for epoch {string}', (epochName) => checkValueForEpoch(epochName, 'contain.text'))

Then('Transition rule is not visible in the table for epoch {string}', (epochName) => checkValueForEpoch(epochName, 'not.contain.text'))

Then('Transition rule is searched', () => cy.searchFor(transitionRule, true))

Then('The transition rule is visible in the correct table column', () => {
    let expectedValue = transitionRule.length < 60 ? transitionRule : `${transitionRule.substring(0, 60)}...`
    cy.checkRowByIndex(0, 'Transition Rule', expectedValue)
})

Then('The transition rule is changed to have {int} characters', (numberOfCharacters) => fillTransitionRule('x'.repeat(numberOfCharacters)))

Then('The warning message about transition rule exceeding 200 characters is displayed', () => cy.contains('[role="alert"]', 'This field must not exceed 200 characters').should('be.visible'))

Then('[API] Link Study Element to Epoch and Study Arm within selected study', () => cy.createDesignMatrix(getCurrStudyUid(), element_uid))

function perfomAction(epochName, actionLocator) {
    cy.contains('table thead th', epochName).invoke('index').then(index => {
        cy.get('table tbody tr').eq(0).find('td').eq(index).find(actionLocator).click()
    })
}

function perfomActionForSpecificBranch(epochName, branchName, actionLocator) {
    cy.contains('table thead th', epochName).invoke('index').then(index => {
        cy.contains('table tbody tr', branchName).find('td').eq(index).find(actionLocator).click()
    })
}

function checkValueForEpoch(epochName, validation) {
    cy.contains('table thead th', epochName).invoke('index').then(index => {
        cy.get('table tbody tr').eq(0).find('td').eq(index).should(validation, `${transitionRule.substring(0, 5)}...`)
    })
}