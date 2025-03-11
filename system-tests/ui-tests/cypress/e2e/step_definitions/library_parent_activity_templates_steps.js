import { objectVersion, objectName } from "../../support/front_end_commands/table_commands"
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

const checkIfValidationAppears = (locator) => cy.elementContain(locator, "This field is required")
let defaultActivityName, newActivityNameUpdated, indicationSelected, version

Given("The activity template exists with a status as {string}", (status) => {
    cy.searchAndGetData(status, 'Parent template').then(() => {
        version = objectVersion
        defaultActivityName = objectName
    })
})

Then("The new Activity is visible in the Activity Templates Table", () => checkTemplateInTable(defaultActivityName, 'Draft', '0.1'))

Then("The updated Activity is visible within the table", () => {
  checkTemplateInTable(newActivityNameUpdated, 'Draft', '0.2')
  cy.checkRowByIndex(0, "Activity", "Not Applicable")
})

Then("The new Activity is visible with Not Applicable indexes in the Activity Templates Table", () => {
  checkTemplateInTable(defaultActivityName, 'Draft', '0.1')
  cy.checkRowByIndex(0, "Activity", "Not Applicable")
})

When("The new activity is added in the library", () => {
  defaultActivityName = `${Date.now()}default`
  addTemplate(defaultActivityName)
  cy.searchAndCheckResults(defaultActivityName)
})

When("The second activity is added with the same template text", () => addTemplate(defaultActivityName))

When("The new Activity is added in the library with not applicable for indexes", () => {
  defaultActivityName = `${Date.now()}default`
  cy.clickButton('add-template');
  fillTemplateNameAndCountinue(defaultActivityName)
  cy.selectFirstVSelect('template-activity-group')
  cy.selectFirstVSelect('template-activity-sub-group')
  cy.checkAllCheckboxes()
  cy.clickFormActionButton('save')
})

When("The activity metadata is updated", () => {
  newActivityNameUpdated = `${Date.now()}Updated`
  fillTemplateNameAndCountinue(newActivityNameUpdated)
  cy.checkAllCheckboxes()
  cy.clickFormActionButton('continue')
  cy.fillInput("template-change-description", "updated for test");
  cy.clickFormActionButton('save')
})

When("The new Activity template is added without template text", () => {
  cy.clickButton('add-template')
  cy.clickFormActionButton('continue')
})

When("The new Activity template is added without Indication or Disorder", () => addTemplateWithoutMandatoryData(false, false, false))

When("The new Activity template is added without Activity Group", () => addTemplateWithoutMandatoryData(true, false, false))

When("The new Activity template is added without Activity Subgroup", () => addTemplateWithoutMandatoryData(true, true, false))

When("The new Activity template is added without Activity field", () => addTemplateWithoutMandatoryData(true, true, true))

Then("The validation appears for Indication or Disorder field", () => checkIfValidationAppears('template-indication-dropdown'))

Then("The validation appears for Activity Group field", () => checkIfValidationAppears('template-activity-group'))

Then("The validation appears for Activity Subgroup field", () => checkIfValidationAppears('template-activity-sub-group'))

Then("The validation appears for Activity field", () => checkIfValidationAppears('template-activity-activity'))

Then("The validation appears for activity change description field", () => checkIfValidationAppears('template-change-description'))

When("The created activity template is edited without change description provided", () => {
  fillTemplateNameAndCountinue("testDescriptionUpdate")
  cy.clickFormActionButton('continue')
  cy.get('[data-cy="template-change-description"] [value]').clear()
  cy.clickFormActionButton('save')
})

Then("The parent activity is no longer available", () => cy.confirmItemNotAvailable(defaultActivityName))

When("The indexing is updated for the Activity Template", () => {
  cy.selectLastVSelect("template-indication-dropdown")
  cy.get('[data-cy="template-indication-dropdown"] .v-field__input').invoke("text").then(text => indicationSelected = text)
  cy.clickButton("save-button")
  cy.checkSnackbarMessage('Indexing properties updated')
  cy.searchAndCheckResults(defaultActivityName)
})

Then("The indexes in activity template are updated", () => {
  cy.get('[data-cy="template-indication-dropdown"] .v-field__input').should('contain', indicationSelected.split(',')[0])
  cy.get('[data-cy="template-indication-dropdown"] .v-field__input').should('contain', indicationSelected.split(',')[1])
})

Then("The activity template has status Draft and version incremented by 0.1", () => cy.checkStatusAndVersion("Draft", version + 0.1))

Then("The activity template has status Retired and the same version as before", () => cy.checkStatusAndVersion("Retired", version))

Then("The activity template has status Final and version 1.0", () => cy.checkStatusAndVersion('Final', '1.0'))

Then("The activity template has status Final and the same version as before", () => cy.checkStatusAndVersion("Final", version))

function fillTemplateNameAndCountinue(name) {
  cy.wait(1500)
  cy.fillTextArea("template-text-field", name)
  cy.clickFormActionButton('continue')
  cy.clickFormActionButton('continue')
}

function addTemplate(name) {
  cy.clickButton('add-template');
  fillTemplateNameAndCountinue(name)
  cy.selectFirstVSelect('template-indication-dropdown')
  cy.selectFirstVSelect('template-activity-group')
  cy.selectFirstVSelect('template-activity-sub-group')
  cy.selectFirstVSelect('template-activity-activity')
  cy.clickFormActionButton('save')
}

function addTemplateWithoutMandatoryData(selectIndication, selectActivityGroup, selectSubGroup) {
  cy.clickButton('add-template')
  fillTemplateNameAndCountinue(`${Date.now()}`)
  if (selectIndication) cy.selectFirstVSelect('template-indication-dropdown')
  if (selectActivityGroup) cy.selectFirstVSelect('template-activity-group')
  if (selectSubGroup) cy.selectFirstVSelect('template-activity-sub-group')
  cy.clickFormActionButton('save')
}

function checkTemplateInTable(name, status, version) {
  cy.wait(1000)
  cy.searchAndCheckResults(name)
  cy.checkRowByIndex(0, "Parent template", name);
  cy.checkStatusAndVersion(status, version)
}
