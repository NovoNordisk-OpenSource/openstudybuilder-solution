
import { fillTemplateName } from './library_syntax_templates_common_steps'
const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')
const { getShortUniqueId } = require("../../support/helper_functions");

let nameSufix = `template ${getShortUniqueId()}`
let objectivePreInstanceName
let preInstanceName
let parameterSelected
let secondParameterSelected

When('The objective pre-instatiation name is set', () => fillBaseData(`Test [Activity] and [ActivityGroup] ${nameSufix}`))

When('The objective pre-instatiation name is updated', () => fillBaseData(`Update${getShortUniqueId()}`))

When('The Radiobutton with value Yes is selected', () => cy.clickButton('radio-Yes'))

When('The template change description is filled in', () => cy.fillInput('template-change-description', 'updated for test'))

When('The pre-instantiation is created from that objective template', () => {
  cy.selectFirstMultipleSelect('Activity')
  cy.selectFirstMultipleSelect('ActivityGroup')
  cy.get('[data-cy="Activity"] .v-input__control  span').invoke('text').then((text) => {
    parameterSelected = text
    secondParameterSelected = text
  })
  cy.get('.fullscreen-dialog .template-readonly p').invoke('text').then(text => preInstanceName = text)
})

Then('The newly added Objective Template Pre-instantiation is visible as a new row in the table', () => {
  cy.get(`[data-cy="search-field"] input`).eq(1).type(preInstanceName)
  cy.checkRowByIndex(0, 'Parent template', preInstanceName)
})

When('The objective pre-instantiation metadata is updated', () => {
  cy.checkLastMultipleSelect('template-indication-dropdown')
})

Then('The Objective pre-instatiation is searched and found', () => {
  cy.searchAndCheckPresence(objectivePreInstanceName, true)
  cy.getRowIndex(0, 'Parent template', objectivePreInstanceName)
})

When('Objective template for pre-instantiation is found by sufix', () => cy.searchAndCheckPresence(nameSufix, true))

function fillBaseData(name) {
  objectivePreInstanceName = name
  fillTemplateName(objectivePreInstanceName)
}
