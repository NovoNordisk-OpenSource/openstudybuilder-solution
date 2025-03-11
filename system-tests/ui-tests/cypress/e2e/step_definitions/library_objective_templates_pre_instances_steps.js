const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')

let defaultObjectivePreInstanceName
let defaultObjectivePreInstanceNameClean
let preInstanceName
let newObjectiveNameUpdated = Date.now() + 'Updated'
let parameterSelected
let secondParameterSelected
let newVersion
let rowIndex

Given('The objective template pre-instance exists with a status as {string}', (status) => {
  cy.getRowIndexByText(status).then(index => {
    rowIndex = index
    cy.getValueFromCellsWithIndex(rowIndex, 8).then((curVersion) => newVersion = parseFloat(curVersion))
  })
})

When('The new objective to be used as pre-instantiation is added in the library', () => {
  defaultObjectivePreInstanceName = "Test [Activity] and [ActivityGroup] template" + Date.now() + 5
  defaultObjectivePreInstanceNameClean = "Test Activity and ActivityGroup template" + Date.now() + 5
  cy.clickButton('add-template');
  cy.fillTextArea('template-text-field', defaultObjectivePreInstanceName)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.get(':nth-child(1) > .v-col-2 > [data-cy="not-applicable-checkbox"] > .v-input__control > .v-selection-control > .v-label').click()
  cy.get(':nth-child(2) > .v-col-2 > [data-cy="not-applicable-checkbox"] > .v-input__control > .v-selection-control > .v-label').click()
  cy.clickButton('radio-Yes')
  cy.clickFormActionButton('save')
})

When('The {string} action is clicked for the created objective template for pre-instantiation', (action) => {
  cy.rowActionsByValue(defaultObjectivePreInstanceNameClean, action)
})

When('The pre-instantiation is created from that objective template', () => {
  cy.rowActionsByValue(defaultObjectivePreInstanceNameClean, 'Create pre-instantiation')
  cy.selectFirstMultipleSelect('Activity')
  cy.selectFirstMultipleSelect('ActivityGroup')
  cy.get('[data-cy="Activity"] .v-input__control  span').invoke('text').then((text) => {
    parameterSelected = text
    secondParameterSelected = text
  })
  cy.get('.fullscreen-dialog .template-readonly p').invoke('text').then(text => preInstanceName = text)
  cy.clickFormActionButton('continue')
  cy.get(':nth-child(1) > .v-col-2 > [data-cy="not-applicable-checkbox"] > .v-input__control > .v-selection-control > .v-label').click()
  cy.get(':nth-child(1) > .v-col-2 > [data-cy="not-applicable-checkbox"] > .v-input__control > .v-selection-control > .v-label').click()
  cy.clickButton('radio-Yes')
  cy.clickFormActionButton('save')
})

Then('The newly added Objective Template Pre-instantiation is visible as a new row in the table', () => {
  cy.clickTab('Pre-instance')
  cy.wait(2000)
  cy.checkRowValueInVisibleTableByColumnIndex(secondParameterSelected.substring(0,3), 2, preInstanceName)
  cy.checkRowValueInVisibleTableByColumnIndex(secondParameterSelected.substring(0,3), 4, 'Draft')
  cy.checkRowValueInVisibleTableByColumnIndex(secondParameterSelected.substring(0,3), 5, '0.1')
})

When('The {string} action is clicked for the objective pre-instantiation', (action) => {
  cy.tableRowActions(rowIndex, action)
})

When('The objective pre-instantiation metadata is updated', () => {
  cy.fillTextArea('template-text-field', newObjectiveNameUpdated)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectLastMultipleSelect('template-indication-dropdown')
  cy.selectRadioGroup('template-confirmatory-testing', 'Yes')
  cy.clickFormActionButton('continue')
  cy.fillInput('template-change-description', 'updated for test')
  cy.clickFormActionButton('save')
})

Then('The updated Objective is visible within the table', () => {
  cy.wait(1500)
  cy.checkRowValueByColumnName(newObjectiveNameUpdated, 'Parent template', newObjectiveNameUpdated)
  cy.checkRowValueByColumnName(newObjectiveNameUpdated, 'Status', 'Draft')
  cy.checkRowValueByColumnName(newObjectiveNameUpdated, 'Version', '0.2')
})
