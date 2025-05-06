const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')

let unitName
const fillConversionFactor = (value) => cy.fillInput('unit-conversion-factor', value)

When('Add unit button is clicked', () => cy.clickButton('add-unit'))

Then('A form for unit creation is opened', () => cy.contains('span.dialog-title', 'Add unit').should('be.visible'))

Then('A form for unit edition is opened', () => cy.contains('span.dialog-title', 'Edit unit').should('be.visible'))

When('Unit mandatory data is filled in', () => fillBasicUnitData())

Then('The newly added unit is visible within the Units table', () => {
  cy.fixture('unitDefinition.js').then((unit) => {
    cy.checkRowByIndex(0, 'Library', 'Sponsor')
    cy.checkRowByIndex(0, 'Name', unitName)
    cy.checkRowByIndex(0, 'Master unit', unit.master_unit)
    cy.checkRowByIndex(0, 'Display unit', unit.display_unit)
    cy.checkRowByIndex(0, 'Unit subsets', unit.unit_subsets)
    cy.checkRowByIndex(0, 'CT Unit terms', unit.ct_units_symbol)
    cy.checkRowByIndex(0, 'Convertible unit', unit.convertible_unit)
    cy.checkRowByIndex(0, 'US conventional unit', unit.us_conventional_unit)
    cy.checkRowByIndex(0, 'Unit dimension', unit.unit_dimension)
    cy.checkRowByIndex(0, 'Legacy code', unit.legacy_code)
    cy.checkRowByIndex(0, 'Conversion factor to master', unit.conversion_factor_to_master)
    cy.checkStatusAndVersion('Draft', '0.1')
  })
})

When('The user tries to create unit without Unit Name, codelist term and library provided', () => {
  cy.clickButton('add-unit')
  cy.clickButton('save-button')
})

When('The new unit is added', () => {
  fillBasicUnitData()
  fillOptionalUnitData()
  saveUnit('added')
})

When('The new unit with already existing name is added', () => {
  fillBasicUnitData(unitName)
  cy.clickButton('save-button')
})

When('The draft unit version is edited and saved with change description', () => {
  fillEditionForm()
  saveUnit('updated')
})

When('The unit edition form is filled with data', () => fillEditionForm())

Then('The validation message appears for unit library field', () => cy.checkIfValidationAppears('unit-library'))

Then('The validation message appears for unit name field', () => cy.checkIfValidationAppears('unit-name'))

Then('The validation message appears for codelist term field', () => cy.checkIfValidationAppears('unit-codelist-term'))

Then('The validation message appears for already existing unit name', () => cy.checkSnackbarMessage(`Unit Definition with ['name: ${unitName}'] already exists.`))

When('Unit is found', () => cy.searchFor(unitName, false))

Then('The Use complex unit conversion toggle is set to false', () => checkComplexUnitConversion(false))

Then('The Use complex unit conversion toggle is set to true', () => checkComplexUnitConversion(true))

Then('Use complex unit conversion option is enabled', () => setComplexUnitConversion(true))

Then('Use complex unit conversion option is disabled', () => setComplexUnitConversion(false))

Then('The Conversion factor to master field is blank', () => cy.get('[data-cy="unit-conversion-factor"] input').should('have.value', ''))

Then('Unit creation is saved without errors', () => saveUnit('added'))

Then('Unit editon is saved without errors', () => saveUnit('updated'))

Then('The unit is not saved', () => cy.searchAndCheckPresence(unitName, false))

Then('The created unit is found in table', () => cy.searchAndCheckPresence(unitName, true))

Then('One unit is found after performing full name search', () => cy.searchAndCheckPresence(unitName, true))

When('Conversion factor to master is filled with numeric value', () => fillConversionFactor(1))

When('Conversion factor to master is filled with text value', () => fillConversionFactor('Test'))

When('[API] Unit in status Draft exists', () => createUnitViaApi())

When('[API] Unit is approved', () => cy.approveUnit())

When('[API] Unit is inactivated', () => cy.inactivateUnit())

Given('[API] First unit for search test is created', () => createUnitViaApi(`SearchTest${Date.now()}`))

Given('[API] Second unit for search test is created', () => cy.createUnit(`SearchTest${Date.now()}`))

Then('An error message appears when I save the unit', () => {
  cy.clickButton('save-button')
  cy.checkSnackbarMessage(`Data validation error`)
})

function fillBasicUnitData(customName = '') {
  cy.clickButton('add-unit')
  cy.wait(1000)
  cy.fixture('unitDefinition.js').then((unit) => {
    unitName = customName ? customName : `Unit${Date.now()}`
    cy.selectVSelect('unit-library', unit.library)
    cy.fillInput('unit-name', unitName)
    cy.selectVSelect('unit-codelist-term', unit.ct_units)
  })
}

function fillOptionalUnitData() {
  cy.fixture('unitDefinition.js').then((unit) => {
    cy.selectVSelect('unit-subset', unit.unit_subsets)
    cy.checkbox('convertible-unit', true)
    cy.checkbox('display-unit', true)
    cy.checkbox('si-unit', true)
    cy.checkbox('us-unit', true)
    cy.selectVSelect('unit-dimension', unit.unit_dimension)
    cy.fillInput('unit-legacy-code', unit.legacy_code)
    cy.fillInput('unit-conversion-factor', unit.conversion_factor_to_master)
  })
}

function createUnitViaApi(customName = '') {
    cy.intercept('/api/concepts/unit-definitions?*').as('getData')
    cy.getCtUnitUid()
    cy.getUnitSubsetUid()
    cy.createUnit(customName)
    cy.getUnitName().then(name => unitName = name)
    cy.wait('@getData', {timeout: 20000})
}

function saveUnit(action) {
  const request = action == 'added' ? '/api/concepts/unit-definitions' : '/api/concepts/unit-definitions/Unit*'
  cy.intercept(request).as('getData')
  cy.clickButton('save-button')
  cy.checkSnackbarMessage(`Unit ${action}`)
  cy.wait('@getData', {timeout: 20000})
}

function setComplexUnitConversion(check) {
  cy.wait(1000)
  cy.get('input[aria-label="Use complex unit conversion"]').then(el => {
    check ? cy.wrap(el).check() : cy.wrap(el).uncheck()
    cy.wrap(el).should((check ? 'be.checked' : 'not.be.checked'))
  })
}

function checkComplexUnitConversion(shouldBeChecked) {
  const validation = shouldBeChecked ? 'be.checked' : 'not.be.checked'
  cy.contains('.v-overlay .v-switch', 'Use complex unit conversion').find('input').should(validation)
}

function fillEditionForm() {
  cy.wait(1500)
  cy.get('.dialog-title').should('contain', 'Edit unit')
  cy.get('[data-cy=unit-name] input').invoke('val').should('not.be.empty')
  cy.get('[data-cy=unit-name] input').invoke('val').should('equal', unitName)
  unitName = `Update ${unitName}`
  cy.fillInput('unit-name', `Update ${unitName}`)
}