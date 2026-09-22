import { formName } from "./library_data_collection_standards_crf_builder_tree_versioning_steps";

const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let formNameDefault, formOidDefault

When('The CRF Form name created via API is updated', () => cy.fillInput('form-oid-name', `Update ${formName}`))

Then('The CRF Form created via API is searched and found', () => cy.searchAndCheckPresence(formName, true))

Then('CRF {string} page is loaded', (tabName) => cy.get('button.v-tab-item--selected').should('have.text', tabName))

When('Created CRF form is found', () => cy.searchAndCheckPresence(formNameDefault, true))

Then('The CRF Form is no longer available', () => cy.searchAndCheckPresence(formOidDefault, false))

When('The Form definition container is filled with data', () => changeFormData(`CrfForm${getShortUniqueId()}`, `CrfForm${getShortUniqueId()}`))

When('The Form metadata are updated and saved', () => changeFormData(`Update ${formNameDefault}`, `Update ${formOidDefault}`))

Then('The New version popup window is displayed', () => {
    cy.contains('.v-overlay__content .v-card-title', 'Creating a new version can affect the following parent elements:').should('be.visible')
    cy.get('.v-skeleton-loader', { timeout: 30000 }).should('not.exist')
})

function changeFormData(formName, formOid) {
    formOidDefault = formName
    formNameDefault = formOid
    cy.fillInput('form-oid-name', formNameDefault)
    cy.fillInput('form-oid', formOidDefault)
}