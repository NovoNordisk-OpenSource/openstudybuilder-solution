import { element_uid } from "../../support/api_requests/study_elements_requests";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid } = require("../../support/helper_functions");

let transitionRule

When('User saves changes made in the edition mode', () => cy.get('button[title="Save"]').click())

When('Transion rules are enabled', () => cy.get('input[title="Enable transition rules mode"]').check())

When('Transion rules are disabled', () => cy.get('input[title="Enable transition rules mode"]').uncheck())

When('Transition rules edit window is opened', () => cy.get('.v-overlay .v-card-title').should('have.text', 'Transition Rule'))

When('{int} element is selected', (elementIndex) => cy.get('.v-select__content .v-list-item').eq(elementIndex).click())

Then('User triggers dropdown for element assignment to epoch {string}', (epochName) => {
    cy.contains('table thead th', epochName).invoke('index').then(index => {
        cy.get('table tbody tr').eq(0).find('td').eq(index).find('[role="combobox"] .v-field__input').click()
    })
})

Then('User triggers dropdown for element assignment to epoch {string}, branch {string}', (epochName, branchName) => perfomActionForSpecificBranch(epochName, branchName, '[role="combobox"] .v-field__input'))

Then('User defines transition rule for epoch {string} as {string}', (epochName, rule) => {
    transitionRule = rule
    fillTransitionRule(epochName, transitionRule)
})

Then('User sets transition rule', () => fillTransitionRule('Transition Rule 1'))

Then('Transition rule is visible in the table for epoch {string}', (epochName) => {
    cy.contains('table thead th', epochName).invoke('index').then(index => {
        cy.get('table tbody tr').eq(0).find('td').eq(index).find('.transitionRuleLabel').should('contain', 'Transition rule')
    })
    cy.contains('.transitionRuleText', transitionRule)
})

Then('Transition rule is not visible in the table for epoch {string}', (epochName) => {
    cy.contains('table thead th', epochName).invoke('index').then(index => {
        cy.get('table tbody tr').eq(0).find('td').eq(index).find('.transitionRuleLabel').should('not.exist')
    })
})

Then('Transition rule is searched', () => cy.searchFor(transitionRule, true))

Then('The transition rule is visible in the correct table column', () => {
    let expectedValue = transitionRule.length < 60 ? transitionRule : `${transitionRule.substring(0, 60)}...`
    cy.checkRowByIndex(0, 'Transition Rule', expectedValue)
})

Then('The transition rule for epoch {string} is defined with {int} characters', (epochName, numberOfCharacters) => fillTransitionRule(epochName, 'x'.repeat(numberOfCharacters)))

Then('The transition rule input for epoch name {string} stops at 200 characters', (epochName) => {
    cy.contains('table thead th', epochName).invoke('index').then(index => {
        cy.get('table tbody tr').eq(0).find('td').eq(index).find('.v-counter').should('have.text', '200 / 200')
        cy.get('table tbody tr').eq(0).find('td').eq(index).find('textarea').eq(0).invoke('val').should('have.length', 200)
    })
})

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

function fillTransitionRule(epochName, transitionRule) {
    cy.contains('table thead th', epochName).invoke('index').then(index => {
        cy.get('table tbody tr').eq(0).find('td').eq(index).find('textarea').eq(0).clear().type(transitionRule, {delay: 0})
    })
}