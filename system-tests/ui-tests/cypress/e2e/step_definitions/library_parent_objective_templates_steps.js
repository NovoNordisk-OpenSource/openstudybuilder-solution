const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')

let defaultObjectiveName, apiObjectiveName, objectiveSequenceNumber
let indicationSelected, categorySelected

When('The objective template is found', () => cy.searchFor(apiObjectiveName))

When('The objective template is not created', () => cy.confirmItemNotAvailable(defaultObjectiveName))

When('The objective template is not updated', () => cy.confirmItemNotAvailable(defaultObjectiveName))

Then('The objective template name is displayed in the table', () => cy.checkRowByIndex(0, 'Parent template', defaultObjectiveName))

When('The latest objective sequence number is saved', () => cy.getCellValue(0, 'Sequence number').then(text => objectiveSequenceNumber = Number(text.replace('O', ''))))

Then('Objective sequence number is incremented', () => cy.getCellValue(0, 'Sequence number').then(text => expect(Number(text.replace('O', ''))).greaterThan(objectiveSequenceNumber)))

Then('The objective template name is checked and user goes to indexes', () => {
  cy.get('[data-cy="template-text-field"] [id="editor"]').invoke('text').then(text => cy.wrap(text).should('equal', defaultObjectiveName))
  cy.contains('.v-stepper-item', 'Index template').click()
})

When('The new objective is added in the library', () => {
  defaultObjectiveName = `Objective${Date.now()}`
  fillTemplateData(defaultObjectiveName)
})

When('The objective template form is filled with data', () => {
  defaultObjectiveName = `Objective${Date.now()}`
  fillTemplateDataWithNoApplicableIndexes(defaultObjectiveName)
})

When('The objective template edition form is filled with data', () => {
  defaultObjectiveName = `CancelEdit${Date.now()}`
  fillTemplateDataWithNoApplicableIndexes(defaultObjectiveName, false)
  cy.clickFormActionButton('continue')
})

When('The second objective is added with the same template text', () => {
  fillTemplateDataWithNoApplicableIndexes(apiObjectiveName)
  cy.clickFormActionButton('save')
})

When('The new Objective is added in the library with not applicable for indexes', () => {
  defaultObjectiveName = `Objective${Date.now()}`
  fillTemplateDataWithNoApplicableIndexes(defaultObjectiveName)
  saveAndSearch(defaultObjectiveName)
})

When('The objective metadata is updated', () => {
  defaultObjectiveName = `Update${Date.now()}`
  startTemplateCreation(defaultObjectiveName, false)
  changeIndexes(true)
  cy.clickFormActionButton('continue')
  cy.fillInput('template-change-description', 'updated for test')
  saveAndSearch(defaultObjectiveName)
})

When('The new Objective template is added without template text', () => {
  cy.clickButton('add-template')
  cy.clickFormActionButton('continue')
})

When('The new Objective template is added without Indication or Disorder', () => {
  startTemplateCreation('test')
  fillIndexingData(false)
  cy.clickFormActionButton('save')
})

When('The new Objective template is added without Objective Category', () => {
  startTemplateCreation('test')
  fillIndexingData(true, false)
  cy.clickFormActionButton('save')
})

Then('The validation appears for template change description field', () => cy.checkIfValidationAppears('template-change-description'))

Then("The validation appears for Objective Category field", () => cy.checkIfValidationAppears('template-objective-category'))

Then('The validation appears for Template name', () => cy.checkIfValidationAppears('template-text-field'))

Then('The objective is no longer available', () => cy.confirmItemNotAvailable(apiObjectiveName))

When('The template is edited witout providing mandatory change description', () => {
  cy.wait(500)
  cy.contains('.v-stepper-item', 'Change description').click()
  cy.clearField('template-change-description')
  cy.clickFormActionButton('save')
})

When('The indexing is updated for the Objective Template', () => {
  changeIndexes(false)
  saveAndSearch(apiObjectiveName)
})

When('The objective indexes edition is initiated', () => {
  changeIndex('template-indication-dropdown', true)
  cy.getText('[data-cy="template-indication-dropdown"] [class$="selection-text"]').then(text => indicationSelected = text)
})

When('The objective indexes are not updated', () => cy.get('[data-cy="form-body"]').should('not.contain', indicationSelected))

Then('The updated indexes in objective template are visible in the form', () => {
  const indications = indicationSelected.split(',')
  const categories = categorySelected.split(',')
  indications.forEach(indication => cy.get('[data-cy="form-body"]').should('contain', indication.trim()))
  categories.forEach(category => cy.get('[data-cy="form-body"]').should('contain', category.trim()))
})

When('[API] Objective template is inactivated', () => cy.inactivateObjective())

When('[API] Approve objective template', () => cy.approveObjective())

When('[API] Create objective template', () => {
  createObjectiveViaApi()
  cy.getObjectiveName().then(name => apiObjectiveName = name.replace('<p>', '').replace('</p>', '').trim())
})

When('[API] Search Test - Create first objective template', () => {
  apiObjectiveName = `SearchTest${Date.now()}`
  createObjectiveViaApi(apiObjectiveName)
})

When('[API] Search Test - Create second objective template', () => createObjectiveViaApi(`SearchTest${Date.now()}`))

function fillTemplateData(name) {
  startTemplateCreation(name)
  fillIndexingData()
  saveAndSearch(name)
}

function fillTemplateDataWithNoApplicableIndexes(name, clickAddButton = true) {
  startTemplateCreation(name, clickAddButton)
  cy.checkAllCheckboxes()
}

function fillIndexingData(addIndication = true, addObjectiveCategory = true) {
  if (addIndication) cy.selectFirstMultipleSelect(`template-indication-dropdown`)
  if (addObjectiveCategory) cy.selectFirstMultipleSelect(`template-objective-category`)
  }

function startTemplateCreation(name, clickAddButton = true) {
  if (clickAddButton) cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', name)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
}

function saveAndSearch(name) {
  cy.clickFormActionButton('save')
  cy.searchFor(name)
}

function changeIndexes(clear) {
  changeIndex('template-indication-dropdown', clear)
  changeIndex('template-objective-category', clear)
  cy.getText('[data-cy="template-indication-dropdown"] [class$="selection-text"]').then(text => indicationSelected = text)
  cy.getText('[data-cy="template-objective-category"] [class$="selection-text"]').then(text => categorySelected = text)
}

function changeIndex(indexLocator, clear) {
  if (clear) cy.clearField(indexLocator)
  cy.selectLastMultipleSelect(indexLocator)
}

function createObjectiveViaApi(customName = '') {
  cy.getInidicationUid()
  cy.getObjectiveCategoryUid()
  cy.createObjective(customName)
}