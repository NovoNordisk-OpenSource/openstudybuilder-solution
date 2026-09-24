const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor')
const { getShortUniqueId } = require("../../support/helper_functions");

let unitName
let library = 'Sponsor', ctUnits = '%', ctUnitsSymbol = '%', unitSubsets = 'Dose Unit'
let unitDimension = 'Degrees', legacyCode = `LegacyCode${getShortUniqueId()}`, conversionFactorToMaster = '1'
let convertableUnit = 'Yes', displayUnit = 'Yes', masterUnit = 'No', usConventionalUnit = 'Yes'

const fillConversionFactor = (value) => cy.fillInput('unit-conversion-factor', value)

When('Add unit button is clicked', () => cy.clickButton('add-unit'))

Then('A form for unit creation is opened', () => cy.contains('span.dialog-title', 'Add unit').should('be.visible'))

Then('A form for unit edition is opened', () => cy.contains('span.dialog-title', 'Edit unit').should('be.visible'))

When('Unit mandatory data is filled in', () => fillBasicUnitData())

Then('The newly added unit is visible within the Units table', () => {
  cy.checkRowByIndex(0, 'Library', library)
  cy.checkRowByIndex(0, 'Name', unitName)
  cy.checkRowByIndex(0, 'Master unit', masterUnit)
  cy.checkRowByIndex(0, 'Display unit', displayUnit)
  cy.checkRowByIndex(0, 'Unit subsets', unitSubsets)
  cy.checkRowByIndex(0, 'CT Unit terms', ctUnitsSymbol)
  cy.checkRowByIndex(0, 'Convertible unit', convertableUnit)
  cy.checkRowByIndex(0, 'US conventional unit', usConventionalUnit)
  cy.checkRowByIndex(0, 'Unit dimension', unitDimension)
  cy.checkRowByIndex(0, 'Legacy code', legacyCode)
  cy.checkRowByIndex(0, 'Conversion factor to master',conversionFactorToMaster)
})

When('The new unit is added', () => {
  fillBasicUnitData()
  fillOptionalUnitData()
})

When('The new unit with already existing name is added', () => fillBasicUnitData(unitName))

When('The unit edition form is filled with data', () => fillEditionForm())

Then('The validation message appears for unit library field', () => cy.checkIfValidationAppears('unit-library'))

Then('The validation message appears for unit name field', () => cy.checkIfValidationAppears('unit-name'))

Then('The validation message appears for codelist term field', () => cy.checkIfValidationAppears('unit-codelist-term'))

Then('The validation message appears for already existing unit name', () => cy.checkSnackbarMessage(`Unit Definition with ['name: ${unitName}'] already exists.`))

When('Unit is found', () => cy.searchAndCheckPresence(unitName, true))

Then('The Use complex unit conversion toggle is set to false', () => checkComplexUnitConversion(false))

Then('The Use complex unit conversion toggle is set to true', () => checkComplexUnitConversion(true))

Then('Use complex unit conversion option is enabled', () => setComplexUnitConversion(true))

Then('Use complex unit conversion option is disabled', () => setComplexUnitConversion(false))

Then('The Conversion factor to master field is blank', () => cy.get('[data-cy="unit-conversion-factor"] input').should('have.value', ''))

Then('The unit is not saved', () => cy.searchAndCheckPresence(unitName, false))

Then('The created unit is found in table', () => cy.searchAndCheckPresence(unitName, true))

Then('One unit is found after performing full name search', () => cy.searchAndCheckPresence(unitName, true))

When('Conversion factor to master is filled with numeric value', () => fillConversionFactor(1))

When('Conversion factor to master is filled with text value', () => fillConversionFactor('Test'))

When('Conversion factor to master field is empty', () => cy.get('[data-cy="unit-conversion-factor"]').should('have.value', ''))

When('Concersion factor to master is empty in the unit table', () => cy.checkRowByIndex(0, 'Conversion factor to master', ''))

When('[API] Unit in status Draft exists', () => createUnitViaApi())

When('[API] Unit is approved', () => cy.approveUnit())

When('[API] Unit is inactivated', () => cy.inactivateUnit())

Given('[API] First unit for search test is created', () => createUnitViaApi(`SearchTest${getShortUniqueId()}`))

Given('[API] Second unit for search test is created', () => cy.createUnit(`SearchTest${getShortUniqueId()}`))

Given('Create unit request is intercepted', () => cy.intercept('/api/concepts/unit-definitions').as('getData'))

Given('Update unit request is intercepted', () => cy.intercept('/api/concepts/unit-definitions/Unit*').as('getData'))

Given('User waits for unit request to finish', () => cy.intercept('/api/concepts/unit-definitions/Unit*').as('getData'))

function fillBasicUnitData(customName = '') {
  cy.wait(1000)
  unitName = customName ? customName : `Unit${getShortUniqueId()}`
  cy.selectVSelect('unit-library', library)
  cy.fillInput('unit-name', unitName)
  cy.selectVSelect('unit-codelist-term', ctUnits)
}

function fillOptionalUnitData() {
  cy.selectVSelect('unit-subset', unitSubsets)
  cy.get('[data-cy="convertible-unit"] input').check()
  cy.get('[data-cy="display-unit"] input').check()
  cy.get('[data-cy="si-unit"] input').check()
  cy.get('[data-cy="us-unit"] input').check()
  cy.selectVSelect('unit-dimension', unitDimension)
  cy.fillInput('unit-legacy-code', legacyCode)
  cy.fillInput('unit-conversion-factor', conversionFactorToMaster)
}

function createUnitViaApi(customName = '') {
    cy.intercept('/api/concepts/unit-definitions?*').as('getData')
    cy.getCtUnitUid()
    cy.getUnitSubsetUid()
    cy.createUnit(customName)
    cy.getUnitName().then(name => unitName = name)
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