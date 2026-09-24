import { activity_uid, group_uid, subgroup_uid } from '../../support/api_requests/library_activities';
import { fillTemplateName, changeIndex } from './library_syntax_templates_common_steps'
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let defaultActivityName

Then('The Activity Instruction template is visible in the table', () => cy.checkRowByIndex(0, 'Parent template', defaultActivityName))

When("The Activity Group index is cleared", () => cy.clearField('template-activity-group'))

When("The Activity Subgroup index is cleared", () => cy.clearField('template-activity-sub-group'))

When("The Activity index is cleared", () => cy.clearField('template-activity-activity'))

Then("The validation appears for Activity field", () => cy.checkIfValidationAppears('template-activity-activity'))

Then("The validation appears for activity template group field", () => cy.checkIfValidationAppears(`template-activity-group`))

Then("The validation appears for activity template subgroup field", () => cy.checkIfValidationAppears(`template-activity-sub-group`))

Then("The activity instruction is searched and found", () => cy.searchAndCheckPresence(defaultActivityName, true))

Then("The parent activity is no longer available", () => cy.searchAndCheckPresence(defaultActivityName, false))

When('The mandatory indexes are filled', () => changeMandatoryIndexes())

When('All activity instruction indexes are filled in', () => {
  changeMandatoryIndexes()
  changeIndex('template-indication-dropdown', false, false)
  changeIndex('template-activity-activity', false, false)
})

When('All activity instruction indexes are cleared and filled in', () => {
  cy.wait(1000)
  cy.selectLastVSelect('template-activity-group')
  changeIndex('template-activity-sub-group', true, true)
  changeIndex('template-indication-dropdown', true, true)
  changeIndex('template-activity-activity', true, true)
})

When('The activity instruction template form is filled with base data', () => fillBaseData(`ActivityInstruction${getShortUniqueId()}`))

When('The activity template metadata update is started', () => fillBaseData(`Update${getShortUniqueId()}`))

When('The activity template edition form is filled with data', () => fillBaseData(`CancelEdit${getShortUniqueId()}`))

When('The activity instruction template form is filled with already existing name', () => fillBaseData(defaultActivityName))

When('User intercepts activity templates request', () => cy.intercept('/api/activity-instruction-templates?page_number=1&*').as('getTemplate'))

When('User waits for activity templates request', () => cy.wait('@getTemplate', {timeout: 20000}))

Then('[API] Activity Instruction in status Draft exists', () => createActivityInstructionViaApi())

Then('[API] Activity Instruction is approved', () => cy.approveActivityInstruction())

Then('[API] Activity Instruction is inactivated', () => cy.inactivateActivityInstruction())

When('[API] Search Test - Create first activity instruction template', () => {
  defaultActivityName = `SearchTest${getShortUniqueId()}`
  createActivityInstructionViaApi(defaultActivityName)
})

When('[API] Search Test - Create second activity instruction template', () => createActivityInstructionViaApi(`SearchTest${getShortUniqueId()}`))

function createActivityInstructionViaApi(customName = '') {
  cy.getInidicationUid()
  cy.createActivityInstruction(group_uid, subgroup_uid, activity_uid, customName)
  cy.getActivityInstructionName().then(name => defaultActivityName = name.replace('<p>', '').replace('</p>', '').trim())
}

function changeMandatoryIndexes() {
  cy.wait(1000)
  cy.get('[data-cy="template-activity-group"] input').clear().type('AE Requiring Additional Data')
  cy.selectFirstVSelect('template-activity-group')
  changeIndex('template-activity-sub-group', false, false)
}

function fillBaseData(name) {
  defaultActivityName = name
  fillTemplateName(name)
}