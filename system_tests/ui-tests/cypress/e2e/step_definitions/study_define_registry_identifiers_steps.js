import { getCurrStudyUid } from '../../support/helper_functions'

const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('[API] Registry Identifier with all values set to null is created', () => cy.nullRegistryIdentifiersForStudy(getCurrStudyUid()))

When('The identifiers are set with following data', (dataTable) => dataTable.hashes().forEach(element => cy.fillInput(element.identifier, element.value)))

Then('The identifiers table is showing following data', (dataTable) => {
    dataTable.hashes().forEach(element => cy.contains('table tbody tr td', element.identifier).next().contains(element.value))
})

Then('The identifiers table is showing following data in column Reason for missing', (dataTable) => {
    dataTable.hashes().forEach(element => cy.contains('table tbody tr td', element.identifier).next().next().contains(element.value, { matchCase: false }))
})
