const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions.js");
import { getCurrStudyUid } from '../../support/helper_functions.js'

export let elementName

Given('[API] Get all Study Elements within selected study', () => cy.getElementsUids(getCurrStudyUid()))

Given('[API] Delete all Study Elements within selected study', () => cy.deleteElements(getCurrStudyUid()))

When('User intercepts the study elements request', () => cy.intercept('/api/studies/*/study-elements?*').as('elements'))

When('User waits for the study elements request', () => cy.wait('@elements'))

When('The element type is set to {string}', (value) => selectValueFromDropdown('Element type', value))

When('The element subtype is set to {string}', (value) => selectValueFromDropdown('Element subtype', value))

When('The element name is set to {string}', (value) => cy.contains('form .v-input', 'Element name').find('input').type(value))

When('The element short name is set to {string}', (value) => cy.contains('form .v-input', 'Element short name').find('input').type(value))

When('[API] Uids are fetched for element subtype {string}', (subtypeName) => cy.getElementTypeAndSubType(subtypeName))

Given('[API] Element is created for the current study', () => {
    cy.addElementToStudy(getCurrStudyUid(), elementName = `El${getShortUniqueId()}`)
})

function selectValueFromDropdown(dropdownName, value) {
    cy.contains('form .v-field', dropdownName).click()
    cy.get('.v-overlay .v-list-item .v-list-item-title').each(el => {
        if (el.text() == value) {
            cy.wrap(el).click() 
            return false
        }
    })
}