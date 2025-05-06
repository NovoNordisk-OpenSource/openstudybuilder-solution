const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')

let defaultEndpointName, apiEndpointName, endpointSequenceNumber
let indicationSelected, categorySelected, subCategorySelected

When('The endpoint template is found', () => cy.searchFor(apiEndpointName))

When('The endpoint template is not created', () => cy.confirmItemNotAvailable(defaultEndpointName))

When('The endpoint template is not updated', () => cy.confirmItemNotAvailable(defaultEndpointName))

Then('The endpoint template name is displayed in the table', () => cy.checkRowByIndex(0, 'Parent template', defaultEndpointName))

When('The latest endpoint sequence number is saved', () => cy.getCellValue(0, 'Sequence number').then(text => endpointSequenceNumber = Number(text.replace('E', ''))))

Then('Endpoint sequence number is incremented', () => cy.getCellValue(0, 'Sequence number').then(text => expect(Number(text.replace('E', ''))).greaterThan(endpointSequenceNumber)))

Then('The endpoint template name is checked and user goes to indexes', () => {
  cy.get('[data-cy="template-text-field"] [id="editor"]').invoke('text').then(text => cy.wrap(text).should('equal', defaultEndpointName))
  cy.contains('.v-stepper-item', 'Index template').click()
})

When('The new endpoint is added in the library', () => {
  defaultEndpointName = `Endpoint${Date.now()}`
  fillTemplateData(defaultEndpointName)
})

When('The endpoint template form is filled with data', () => {
  defaultEndpointName = `Endpoint${Date.now()}`
  fillTemplateDataWithNoApplicableIndexes(defaultEndpointName)
})

When('The endpoint template edition form is filled with data', () => {
  defaultEndpointName = `CancelEdit${Date.now()}`
  fillTemplateDataWithNoApplicableIndexes(defaultEndpointName, false)
  cy.clickFormActionButton('continue')
})

When('The second endpoint is added with the same template text', () => {
  fillTemplateDataWithNoApplicableIndexes(apiEndpointName)
  cy.clickFormActionButton('save')
})

When('The new Endpoint is added in the library with not applicable for indexes', () => {
  defaultEndpointName = `Endpoint${Date.now()}`
  fillTemplateDataWithNoApplicableIndexes(defaultEndpointName)
  saveAndSearch(defaultEndpointName)
})

Then('The template has not applicable selected for all indexes', () => {
  cy.contains('.v-stepper-item', 'Index template').click()
  cy.get('.v-sheet .v-window [type="checkbox"]').each(checkbox => cy.wrap(checkbox).should('be.checked'))
})

When('The endpoint metadata is updated', () => {
  defaultEndpointName = `Update${Date.now()}`
  startTemplateCreation(defaultEndpointName, false)
  changeIndexes(true)
  cy.clickFormActionButton('continue')
  cy.fillInput('template-change-description', 'updated for test')
  saveAndSearch(defaultEndpointName, 'Endpoint template updated')
})

When('The new Endpoint template is added without template text', () => {
  cy.clickButton('add-template')
  cy.clickFormActionButton('continue')
})

When('The new Endpoint template is added without Indication or Disorder', () => fillTemplateIndexesIncorrectly(false))

When('The new Endpoint template is added without Endpoint Category', () => fillTemplateIndexesIncorrectly(true, false))

When('The new Endpoint template is added without Endpoint Subcategory', () => fillTemplateIndexesIncorrectly(true, true, false))

Then('The validation appears for Endpoint Category field', () => cy.checkIfValidationAppears('template-endpoint-category'))

Then('The validation appears for Endpoint Subcategory field', () => cy.checkIfValidationAppears('template-endpoint-sub-category'))

Then('The endpoint is no longer available', () => cy.confirmItemNotAvailable(apiEndpointName))

When('The indexing is updated for the Endpoint Template', () => {
  changeIndexes(false)
  saveAndSearch(apiEndpointName, 'Indexing properties updated')
})

When('The endpoint indexes edition is initiated', () => {
  changeIndex('template-indication-dropdown', true)
  cy.getText('[data-cy="template-indication-dropdown"] [class$="selection-text"]').then(text => indicationSelected = text)
})

When('The endpoint indexes are not updated', () => cy.get('[data-cy="form-body"]').should('not.contain', indicationSelected))

Then('The indexes in endpoint template are updated', () => {
  const indications = indicationSelected.split(',')
  const cateogories = categorySelected.split(',')
  const subCateogories = subCategorySelected.split(',')
  indications.forEach(indication => cy.get('[data-cy="form-body"]').should('contain', indication.trim()))
  cateogories.forEach(category => cy.get('[data-cy="form-body"]').should('contain', category.trim()))
  subCateogories.forEach(subgategory => cy.get('[data-cy="form-body"]').should('contain', subgategory.trim()))
})

When('[API] Endpoint template is inactivated', () => cy.inactivateEndpoint())

When('[API] Approve endpoint template', () => cy.approveEndpoint())

When('[API] Create endpoint template', () => {
  createEndpointViaApi()
  cy.getEndpointName().then(name => apiEndpointName = name.replace('<p>', '').replace('</p>', '').trim())
})

When('[API] Search Test - Create first endpoint template', () => {
  apiEndpointName = `SearchTest${Date.now()}`
  createEndpointViaApi(apiEndpointName)
})

When('[API] Search Test - Create second endpoint template', () => createEndpointViaApi(`SearchTest${Date.now()}`))

function fillTemplateData(name) {
  startTemplateCreation(name)
  fillIndexingData()
  saveAndSearch(name)
}

function fillTemplateDataWithNoApplicableIndexes(name, clickAddButton = true) {
  startTemplateCreation(name, clickAddButton)
  cy.checkAllCheckboxes()
}

function fillTemplateIndexesIncorrectly(addIndication = true, addEndpointCategory = true, addEndpointSubCategory = true) {
  startTemplateCreation('test')
  fillIndexingData(addIndication, addEndpointCategory, addEndpointSubCategory)
  cy.clickFormActionButton('save')
}

function fillIndexingData(addIndication = true, addEndpointCategory = true, addEndpointSubCategory = true) {
  if (addIndication) cy.selectFirstMultipleSelect(`template-indication-dropdown`)
  if (addEndpointCategory) cy.selectFirstMultipleSelect(`template-endpoint-category`)
  if (addEndpointSubCategory) cy.selectFirstMultipleSelect('template-endpoint-sub-category')
}

function startTemplateCreation(name, clickAddButton = true) {
  if (clickAddButton) cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', name)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
}

function saveAndSearch(name, action = 'add') {
  let message = action === 'add' ? 'Endpoint template added' : action
  cy.clickFormActionButton('save')
  cy.checkSnackbarMessage(message)
  cy.searchFor(name)
}

function changeIndexes(clear) {
  changeIndex('template-indication-dropdown', clear)
  changeIndex('template-endpoint-category', clear)
  changeIndex('template-endpoint-sub-category', clear)
  cy.getText('[data-cy="template-indication-dropdown"] [class$="selection-text"]').then(text => indicationSelected = text)
  cy.getText('[data-cy="template-endpoint-category"] [class$="selection-text"]').then(text => categorySelected = text)
  cy.getText('[data-cy="template-endpoint-sub-category"] [class$="selection-text"]').then(text => subCategorySelected = text)
}

function changeIndex(indexLocator, clear) {
  if (clear) cy.clearField(indexLocator)
  cy.selectLastMultipleSelect(indexLocator)
}

function createEndpointViaApi(customName = '') {
  cy.getInidicationUid()
  cy.getEndpointCategoryUid()
  cy.getEndpointSubCategoryUid()
  cy.createEndpoint(customName)
}
