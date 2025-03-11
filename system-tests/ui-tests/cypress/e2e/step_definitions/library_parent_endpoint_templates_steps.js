const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')

let defaultEndpointName
let newEndpointName2 = Date.now() + 10
let newEndpointNameUpdated = Date.now() + 'Updated'
let randomParamEndpointTemplate = 'Test [Activity] and [Event] template' + Date.now() + 15
let indicationSelected
let endpointCatSelected
let endpointSubCatSelected
let parameterSelected
let newVersion
let rowIndex

Given('The endpoint template exists with a status as {string}', (status) => {
  cy.getRowIndexByText(status).then(index => {
    rowIndex = index
    cy.getValueFromCellsWithIndex(rowIndex, 5).then((curVersion) => newVersion = parseFloat(curVersion))
  })
})

When('The new endpoint is added in the library', () => {
  defaultEndpointName = Date.now() + 5
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', defaultEndpointName)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectFirstMultipleSelect('template-indication-dropdown')
  cy.get('[data-cy="template-indication-dropdown"] > .v-input__control > .v-field > .v-field__field > .v-field__input > .v-autocomplete__selection > .v-autocomplete__selection-text')
    .invoke('text')
    .then((text) => {
      indicationSelected = text
    })
  cy.selectFirstMultipleSelect('template-endpoint-category')
  cy.get('[data-cy="template-endpoint-category"] > .v-input__control > .v-field > .v-field__field > .v-field__input > .v-autocomplete__selection > .v-autocomplete__selection-text')
    .invoke('text')
    .then((text) => {
      endpointCatSelected = text
    })
  cy.selectFirstMultipleSelect('template-endpoint-sub-category')
  cy.get('[data-cy="template-endpoint-sub-category"] > .v-input__control > .v-field > .v-field__field > .v-field__input > .v-autocomplete__selection > .v-autocomplete__selection-text')
    .invoke('text')
    .then((text) => {
      endpointSubCatSelected = text
    })

    cy.clickFormActionButton('save')
})

When('The second endpoint is added with the same template text', () => {
  cy.wait(1500)
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', defaultEndpointName)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.checkAllCheckboxes()

  cy.clickFormActionButton('save')
})

Then('The new Endpoint is visible in the Endpoint Templates Table', () => {
  cy.checkRowValueByColumnName(defaultEndpointName, 'Parent template', defaultEndpointName)
  cy.checkRowValueByColumnName(defaultEndpointName, 'Status', 'Draft')
  cy.checkRowValueByColumnName(defaultEndpointName, 'Version', '0.1')
})

Then('The validation appears for Template Text field', () => {
  cy.elementContain('form-body', 'This field is required')
})

When('The new Endpoint is added in the library with not applicable for indexes', () => {
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', newEndpointName2)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.checkAllCheckboxes()
  cy.clickFormActionButton('save')
})

Then('The new Endpoint is visible with Not Applicable indexes in the Endpoint Templates Table', () => {
  cy.checkRowValueByColumnName(newEndpointName2, 'Parent template', newEndpointName2)
  cy.checkRowValueByColumnName(newEndpointName2, 'Status', 'Draft')
  cy.checkRowValueByColumnName(newEndpointName2, 'Version', '0.1')
})

When('The {string} action is clicked for the endpoint', (action) => {
  cy.tableRowActions(rowIndex, action)
})

When('The {string} action is clicked for the created endpoint with parameters', (action) => {
  cy.rowActionsByValue(randomParamEndpointTemplate, action)
})

When('The {string} action is clicked for the created endpoint', (action) => {
  cy.waitForTable()
  cy.wait(1000)
  cy.rowActionsByValue(defaultEndpointName, action)
})

When('The endpoint metadata is updated', () => {
  cy.wait(1500)
  cy.fillTextArea('template-text-field', newEndpointNameUpdated)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectLastMultipleSelect('template-indication-dropdown')
  cy.get('[data-cy="not-applicable-checkbox"] input').eq(1).click()
  cy.selectLastMultipleSelect('template-endpoint-sub-category')
  cy.clickFormActionButton('continue')
  cy.fillInput('template-change-description', 'updated for test')
  cy.clickFormActionButton('save')
})

Then('The updated Endpoint is visible within the table', () => {
  cy.wait(1500)
  cy.checkRowValueByColumnName(newEndpointNameUpdated, 'Parent template', newEndpointNameUpdated)
  cy.checkRowValueByColumnName(newEndpointNameUpdated, 'Status', 'Draft')
  cy.checkRowValueByColumnName(newEndpointNameUpdated, 'Version', '0.2')
})

When('The new Endpoint template is added without template text', () => {
  cy.clickButton('add-template')
  cy.clickFormActionButton('continue')
})

When('The new Endpoint template is added without Indication or Disorder', () => {
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', newEndpointNameUpdated)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectLastMultipleSelect('template-endpoint-category')
  cy.selectFirstMultipleSelect('template-endpoint-sub-category')
  cy.clickFormActionButton('save')
})

When('The new Endpoint template is added without Endpoint Category', () => {
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', newEndpointNameUpdated)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectFirstMultipleSelect('template-indication-dropdown')
  cy.selectFirstMultipleSelect('template-endpoint-sub-category')
  cy.clickFormActionButton('save')
})

When('The new Endpoint template is added without Endpoint Subcategory', () => {
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', newEndpointNameUpdated)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectFirstMultipleSelect('template-indication-dropdown')
  cy.selectLastMultipleSelect('template-endpoint-category')
  cy.clickFormActionButton('save')
})

Then('The validation appears for Endpoint Category field', () => {
  cy.elementContain('template-endpoint-category', 'This field is required').should('be.visible')
})

Then('The validation appears for Endpoint Subcategory field', () => {
  cy.elementContain('template-endpoint-sub-category', 'This field is required').should('be.visible')
})

When('The new Endpoint text is created with a parameters', () => {
  cy.clickButton('add-template')
  cy.fillTextArea('template-text-field', randomParamEndpointTemplate)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectFirstMultipleSelect('template-indication-dropdown')
  cy.selectFirstMultipleSelect('template-endpoint-category')
  cy.clickFormActionButton('save')
})

Then('The status of the template displayed as Final with a version rounded up to 1.0', () => {
  cy.checkRowValueByColumnName(defaultEndpointName, 'Status', 'Final')
  cy.checkRowValueByColumnName(defaultEndpointName, 'Version', '1.0')
})

When('The created endpoint template is edited without change description provided', () => {
  cy.fillTextArea('template-text-field', 'testDescriptionUpdate')
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
  cy.selectLastMultipleSelect('template-indication-dropdown')
  cy.selectLastMultipleSelect('template-endpoint-category')
  cy.clickFormActionButton('continue')
  cy.clearField("template-change-description")
  cy.clickFormActionButton('save')
})

Then('The validation appears for endpoint change description field', () => {
  cy.contains('.v-messages__message', 'This field is required').should('be.visible')
})

Then('The endpoint is no longer available', () => {
  cy.wait(500)
  cy.contains(defaultEndpointName).should('not.exist')
})

When('The indexing is updated for the Endpoint Template', () => {
  cy.selectLastMultipleSelect('template-indication-dropdown')
  cy.selectLastMultipleSelect('template-endpoint-category')
  cy.get('[data-cy="template-indication-dropdown"] > .v-input__control > .v-field > .v-field__field > .v-field__input >')
    .invoke('text')
    .then((text) => {
      indicationSelected = text
    })
    cy.get('[data-cy="template-endpoint-category"] > .v-input__control > .v-field > .v-field__field > .v-field__input >')
    .invoke('text')
    .then((text) => {
      endpointCatSelected = text
    })
    cy.clickFormActionButton('save')
})

Then('The indexes in endpoint template are updated', () => {
  const indications = indicationSelected.split(',')
  const endpoints = endpointCatSelected.split(',')
  indications.forEach(indication => cy.get('[data-cy="form-body"]').should('contain', indication.trim()));
  endpoints.forEach(endpoint => cy.get('[data-cy="form-body"]').should('contain', endpoint.trim()));
})

Then('The endpoint template is updated to draft with version incremented by 0.1', () => {
  cy.wait(4000)
  cy.checkRowByIndex(rowIndex, 'Status', 'Draft')
  cy.checkRowByIndex(rowIndex, 'Version', newVersion + 0.1)
})

Then('The endpoint template is displayed with a status as Retired with the same version as before', () => {
  cy.wait(4000)
  cy.checkRowByIndex(rowIndex, 'Status', 'Retired')
  cy.checkRowByIndex(rowIndex, 'Version', newVersion)
})

Then('The endpoint template is displayed with a status as Final with the same version as before', () => {
  cy.wait(4000)
  cy.checkRowByIndex(rowIndex, 'Status', 'Final')
  cy.checkRowByIndex(rowIndex, 'Version', newVersion)
})
