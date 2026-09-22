import { itemName } from "./library_data_collection_standards_crf_builder_tree_versioning_steps";

const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let crfItemName, crfItemOid

When('User goes to {string} step of crf item creation', (name) => cy.contains('.v-stepper-item', name).click())

When('The CRF Item datatype is set as {string}', (type) => cy.selectVSelect('item-data-type', type))

When('User waits for CRF Items data to load', () => {
    cy.intercept('/api/odms/items?*').as('getData')
    cy.wait('@getData', { timeout: 90000 })
})

When('The CRF Item created via API is searched and found', () => cy.searchAndCheckPresence(itemName, true))

When('The CRF Item created via API is searched and not found', () => cy.searchAndCheckPresence(itemName, false))

When('The CRF Item name created via API is updated', () => cy.fillInput('item-name', `Update ${itemName}`))

When('Created CRF Item is found', () => cy.searchAndCheckPresence(crfItemName, true))

Then("The CRF Item is visible in the table", () => {
    cy.checkRowByIndex(0, 'OID', crfItemOid)
    cy.checkRowByIndex(0, 'Name',crfItemName)
})

When('The CRF Item name is set', () => cy.fillInput('item-name', crfItemName = `CrfItem${getShortUniqueId()}`))

When('The CRF Item oid is set', () => cy.fillInput('item-oid', crfItemOid = `Oid${getShortUniqueId()}`))

When('The CRF Item name is updated', () => cy.fillInput('item-name', crfItemName += 'Update'))

When('The CRF Item oid is updated', () => cy.fillInput('item-oid', crfItemOid += 'Update'))