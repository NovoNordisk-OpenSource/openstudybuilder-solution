import { itemGroupName } from "./library_data_collection_standards_crf_builder_tree_versioning_steps";

const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let itemGroupNameDefault, itemGroupOidDefault

When('The CRF Item Group name created via API is updated', () => cy.fillInput('item-group-name', `Update ${itemGroupName}`))

When('The CRF Item Group created via API is searched and found', () => cy.searchAndCheckPresence(itemGroupName, true))

When('Created CRF Item Group is found', () => cy.searchAndCheckPresence(itemGroupNameDefault, true))

Then('The CRF Item Group is no longer available', () => cy.searchAndCheckPresence(itemGroupNameDefault, false))

When('The CRF Item Group definition container is filled with data', () => {
    itemGroupNameDefault = `CrfItemGroup${getShortUniqueId()}`
    itemGroupOidDefault = `Oid${getShortUniqueId()}`
    cy.fillInput('item-group-oid', itemGroupOidDefault)
    cy.fillInput('item-group-name', itemGroupNameDefault)
})

When('The CRF Item Group metadata are updated', () => {
    itemGroupNameDefault = `Update ${itemGroupNameDefault}`
    itemGroupOidDefault = `Update ${itemGroupNameDefault}`
    cy.fillInput('item-group-oid', itemGroupOidDefault)
    cy.fillInput('item-group-name', itemGroupNameDefault)
})

Then('The Item Group approval dialog is displayed', () => {
    // Selecting the dialog card based on its classes
    cy.get('.v-card.v-theme--NNCustomLightTheme')
      .should('be.visible') // Assert that the dialog is visible
      .and('contain', 'Approving the item group will approve the following child elements:'); // Assert that it contains specific text
});
