const { When, Then } = require('@badeball/cypress-cucumber-preprocessor')

let unitName, initialVersion, newUnitName

Then('The newly added unit is visible within the Units table', () => {
  cy.searchAndCheckResults(unitName)
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

When('The new unit is added', () => {
  cy.wait(3000)
  fillBasicUnitData(true, true)
  fillOptionalUnitData()
  cy.clickButton('save-button')
  cy.checkSnackbarMessage('Unit added')
  cy.wait(2000)
})

When('Unit in Draft status is created', () => {
  cy.wait(3000)
  fillBasicUnitData(true, true)
  cy.clickButton('save-button')
  cy.checkSnackbarMessage('Unit added')
  cy.wait(2000)
})

When('The user tries to create unit without Unit Name provided', () => {
  fillBasicUnitData(false, true)
  fillOptionalUnitData()
  cy.clickButton('save-button')
})

When('The user tries to create unit without Unit codelist term provided', () => {
  fillBasicUnitData(true, false)
  fillOptionalUnitData()
  cy.clickButton('save-button')
})

Then('The validation appears for Unit Name field', () => cy.get('.v-input__details').should('contain', 'This field is required'))

Then('The validation appears for Unit codelist term field', () => cy.get('.v-input__details').should('contain', 'This field is required'))

When('The draft unit version is edited and saved with change description', () => {
  newUnitName = `Update ${Date.now()}`
  cy.wait(1500)
  cy.get('.dialog-title').should('contain', 'Edit unit')
  cy.get('[data-cy=unit-name] input').invoke('val').should('not.be.empty')
  cy.get('[data-cy=unit-name] input').invoke('val').should('equal', unitName.toString())
  cy.fillInput('unit-name', newUnitName)
  cy.clickButton('save-button')
  cy.wait(3000)
})

When('The {string} action is clicked for the Unit', (action) => {
  cy.searchAndCheckResults(unitName)
  cy.getCellValue(0, 'Version').then(curVersion => initialVersion = parseFloat(curVersion))
  cy.performActionOnSearchedItem(action)
})

Then('The Unit status is kept as {string} and version is incremented by {string}', (status, increment) => {
  searchAndCheckStatusAndVersion(newUnitName, status, (initialVersion + parseFloat(increment)).toFixed(1))
})

Then('The Unit status is changed to {string} and version remain unchanged', (status) => {
  searchAndCheckStatusAndVersion(unitName, status, initialVersion)
})

Then('The Unit status is changed to {string} and version is incremented by {string}', (status, increment) => {
  searchAndCheckStatusAndVersion(unitName, status,  (initialVersion + parseFloat(increment)).toFixed(1))
})

Then('The Unit status is changed to {string} and version is rounded up to full number', (status) => {
  searchAndCheckStatusAndVersion(unitName, status, Math.ceil(initialVersion))
})

function searchAndCheckStatusAndVersion(name, status, version) {
  cy.searchAndCheckResults(name)
  cy.checkRowByIndex(0, 'Status', status)
  cy.checkRowByIndex(0, 'Version', version)
}

function fillBasicUnitData(setName, setCodelistTerm) {
  cy.clickButton('add-unit')
  cy.wait(3000)
  cy.fixture('unitDefinition.js').then((unit) => {
    unitName = Date.now()
    cy.selectVSelect('unit-library', unit.library)
    if (setName) cy.fillInput('unit-name', unitName)
    if (setCodelistTerm) cy.selectVSelect('unit-codelist-term', unit.ct_units)
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
