import { collectionName } from "./library_data_collection_standards_crf_builder_tree_versioning_steps";

const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let crfTemplateName, crfTemplateOid, effectiveDate = 10, retiredDate = 15

When('The CRF Collection created via API is searched and found', () => cy.searchAndCheckPresence(collectionName, true))

When('Created CRF Collection is found', () => cy.searchAndCheckPresence(crfTemplateName, true))

Then('The CRF Collection is no longer available', () => cy.searchAndCheckPresence(crfTemplateName, false))

Given('[API] The CRF Collection in draft status exists', () => {
    crfTemplateName = `API_CrfItem${getShortUniqueId()}`
    cy.createCrfCollection(crfTemplateName)
})

When('The CRF Collection definition container is filled with data', () => {
    crfTemplateName = `CrfItem${getShortUniqueId()}`
    crfTemplateOid = `Oid${getShortUniqueId()}`
    fillNameAndOid()
    cy.selectDatePicker('crf-collection-effective-date', effectiveDate)
    cy.selectDatePicker('crf-collection-retired-date', retiredDate)
})

When('The CRF Collection metadata are updated', () => {
    crfTemplateName += 'Update'
    crfTemplateOid += 'Update'
    effectiveDate += 1
    retiredDate += 1
    fillNameAndOid()
    cy.selectDatePicker('crf-collection-effective-date', effectiveDate)
    cy.selectDatePicker('crf-collection-retired-date', retiredDate)
})

Then('The CRF Collection is visible in the table', () => {
    cy.checkRowByIndex(0, 'Name', crfTemplateName)
    cy.checkRowByIndex(0, 'OID', crfTemplateOid)
    cy.checkRowByIndex(0, 'Effective', effectiveDate)
    cy.checkRowByIndex(0, 'Obsolete', retiredDate)
})

Then('The validation appears for the CRF Collection Name field', () => cy.get('.v-messages__message').should('be.visible'))

Then('The approval popup window is displayed', () => {
    // Check that the dialog is visible
    cy.get('.v-card.v-theme--NNCustomLightTheme')
      .should('be.visible') // Assert that the dialog is visible
      .and('contain', 'Approving the element will approve the following child elements:'); // Check that it contains the specific text
});

function fillNameAndOid() {
    cy.wait(1000)
    cy.fillInput('crf-collection-oid', crfTemplateOid)
    cy.fillInput('crf-collection-name', crfTemplateName)
}