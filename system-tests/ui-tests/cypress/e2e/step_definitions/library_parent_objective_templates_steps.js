const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')

let defaultObjectiveName
let newObjectiveName2 = Date.now() + 10
let newObjectiveNameUpdated = Date.now() + 'Updated'
let randomParamObjectiveTemplate = 'Test [Activity] and [Event] template' + Date.now() + 15
let indicationSelected
let objectiveCatSelected
let parameterSelected
let newVersion
let rowIndex

Given('The objective template exists with a status as {string}', (status) => {
  cy.getRowIndexByText(status).then(index => {
    rowIndex = index
    cy.getValueFromCellsWithIndex(rowIndex, 5).then((curVersion) => newVersion = parseFloat(curVersion))
  })
})

Given('The objective template exists with a status as Final', () => {
  cy.getRowIndexByText('Draft').then(index => {
    rowIndex = index
    cy.tableRowActions(rowIndex, 'Approve')
    cy.wait(1000)
  })

  cy.getRowIndexByText('Final').then(index => {
    rowIndex = index
    cy.getValueFromCellsWithIndex(rowIndex, 5).then((curVersion) => newVersion = parseFloat(curVersion))
  })
})

When('The new objective is added in the library', () => {
  defaultObjectiveName = Date.now() + 5
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', defaultObjectiveName)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectFirstMultipleSelect('template-indication-dropdown')
  cy.get('[data-cy="template-indication-dropdown"] > .v-input__control > .v-field > .v-field__field > .v-field__input > .v-autocomplete__selection > .v-autocomplete__selection-text')
    .invoke('text')
    .then((text) => {
      indicationSelected = text
    })
  cy.selectFirstMultipleSelect('template-objective-category')
  cy.get('[data-cy="template-objective-category"] > .v-input__control > .v-field > .v-field__field > .v-field__input > .v-autocomplete__selection > .v-autocomplete__selection-text')
    .invoke('text')
    .then((text) => {
      objectiveCatSelected = text
    })
  cy.selectRadioGroup('template-confirmatory-testing', 'Yes')
  cy.clickFormActionButton('save')
})

When('The second objective is added with the same template text', () => {
  cy.wait(1000)
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', defaultObjectiveName)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.checkAllCheckboxes()
  cy.selectRadioGroup('template-confirmatory-testing', 'Yes')
  cy.clickFormActionButton('save')
})

Then('The new Objective is visible in the Objective Templates Table', () => {
  cy.checkRowValueByColumnName(defaultObjectiveName, 'Parent template', defaultObjectiveName)
  cy.checkRowValueByColumnName(defaultObjectiveName, 'Status', 'Draft')
  cy.checkRowValueByColumnName(defaultObjectiveName, 'Version', '0.1')
})

When('The new Objective is added in the library with not applicable for indexes', () => {
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', newObjectiveName2)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.checkAllCheckboxes()
  cy.selectRadioGroup('template-confirmatory-testing', 'Yes')
  cy.clickFormActionButton('save')
})

Then('The new Objective is visible with Not Applicable indexes in the Objective Templates Table', () => {
  cy.checkRowValueByColumnName(newObjectiveName2, 'Parent template', newObjectiveName2)
  cy.checkRowValueByColumnName(newObjectiveName2, 'Status', 'Draft')
  cy.checkRowValueByColumnName(newObjectiveName2, 'Version', '0.1')
})

When('The {string} action is clicked for the objective', (action) => {
  cy.getCellValue(rowIndex, 'Parent template').then(name => {
    cy.tableRowActions(rowIndex, action)
    cy.wait(1000)
    cy.getRowIndexByText(name).then(index => rowIndex = index)
  })
})

When('The {string} action is clicked for the created objective with parameters', (action) => {
  cy.rowActionsByValue(randomParamObjectiveTemplate, action)
  cy.getRowIndexByText(randomParamObjectiveTemplate).then(index => rowIndex = index)
})

When('The {string} action is clicked for the created objective', (action) => {
  cy.rowActionsByValue(defaultObjectiveName, action)
  cy.getRowIndexByText(defaultObjectiveName).then(index => rowIndex = index)
})

When('The objective metadata is updated', () => {
  cy.fillTextArea('template-text-field', newObjectiveNameUpdated)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectLastMultipleSelect('template-indication-dropdown')
  cy.checkAllCheckboxes()
  cy.clickFormActionButton('continue')
  cy.fillInput('template-change-description', 'updated for test')
  cy.clickFormActionButton('save')
})

Then('The updated Objective Template is visible within the table', () => {
  cy.wait(1500)
  cy.checkRowValueByColumnName(newObjectiveNameUpdated, 'Parent template', newObjectiveNameUpdated)
  cy.checkRowValueByColumnName(newObjectiveNameUpdated, 'Status', 'Draft')
  cy.checkRowValueByColumnName(newObjectiveNameUpdated, 'Version', '0.2')
})

When('The new Objective template is added without template text', () => {
  cy.clickButton('add-template')
  cy.clickFormActionButton('continue')
})

When('The new Objective template is added without Indication or Disorder', () => {
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', newObjectiveNameUpdated)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectLastMultipleSelect('template-objective-category')
  cy.selectRadioGroup('template-confirmatory-testing', 'Yes')
  cy.clickFormActionButton('save')
})

When('The new Objective template is added without Objective Category', () => {
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', newObjectiveNameUpdated)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectFirstMultipleSelect('template-indication-dropdown')
  cy.selectRadioGroup('template-confirmatory-testing', 'Yes')
  cy.clickFormActionButton('save')
})

Then('The validation appears for Objective Category field', () => {
  cy.elementContain('template-objective-category', 'This field is required').should('be.visible')
})

When('The new Objective text is created with a parameters', () => {
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', randomParamObjectiveTemplate)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectFirstMultipleSelect('template-indication-dropdown')
  cy.selectFirstMultipleSelect('template-objective-category')
  cy.selectRadioGroup('template-confirmatory-testing', 'No')
  cy.clickFormActionButton('save')
})

Then('The status of the parent objective template displayed as Final with a version rounded up to full number', () => {
  cy.checkRowValueByColumnName(defaultObjectiveName, 'Status', 'Final')
  cy.checkRowValueByColumnName(defaultObjectiveName, 'Version', 1)
})

When('The created objective template is edited without change description provided', () => {
  cy.fillTextArea('template-text-field', 'testDescriptionUpdate')
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectLastMultipleSelect('template-indication-dropdown')
  cy.selectLastMultipleSelect('template-objective-category')
  cy.clickFormActionButton('continue')
  cy.clearField('template-change-description')
  cy.clickFormActionButton('save')
})

Then('The validation appears for objective change description field', () => {
  cy.contains('.v-messages__message', 'This field is required').should('be.visible')
})

Then('The objective is no longer available', () => {
  cy.wait(500)
  cy.contains(defaultObjectiveName).should('not.exist')
})

When('The indexing is updated for the Objective Template', () => {
  cy.clearField('template-indication-dropdown')
  cy.clearField('template-objective-category')
  cy.selectLastMultipleSelect('template-indication-dropdown')
  cy.selectLastMultipleSelect('template-objective-category')
  cy.get('[data-cy="template-indication-dropdown"] > .v-input__control > .v-field > .v-field__field > .v-field__input > .v-autocomplete__selection > .v-autocomplete__selection-text')
    .invoke('text')
    .then((text) => {
      indicationSelected = text
    })
    cy.get('[data-cy="template-objective-category"] > .v-input__control > .v-field > .v-field__field > .v-field__input > .v-autocomplete__selection > .v-autocomplete__selection-text')
    .invoke('text')
    .then((text) => {
      objectiveCatSelected = text
    })
    cy.clickFormActionButton('save')
})

Then('The updated indexes in objective template are visible in the form', () => {
  cy.get('[data-cy="form-body"]').should('contain', indicationSelected)
  cy.get('[data-cy="form-body"]').should('contain', objectiveCatSelected)
})

Then('The objective template is updated to draft with version incremented by 0.1', () => {
  cy.wait(1500)
  cy.checkRowByIndex(rowIndex, 'Status', 'Draft')
  cy.checkRowByIndex(rowIndex, 'Version', newVersion + 0.1)
})

Then('The objective template is displayed with a status as Retired with the same version as before', () => {
  cy.wait(1500)
  cy.checkRowByIndex(rowIndex, 'Status', 'Retired')
  cy.checkRowByIndex(rowIndex, 'Version', newVersion)
})

Then('The objective template is displayed with a status as Final with the same version as before', () => {
  cy.wait(2000)
  cy.checkRowByIndex(rowIndex, 'Status', 'Final')
  cy.checkRowByIndex(rowIndex, 'Version', newVersion)
})
