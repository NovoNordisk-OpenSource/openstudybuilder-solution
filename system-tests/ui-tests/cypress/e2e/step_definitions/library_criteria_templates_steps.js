import { objectVersion, objectName } from "../../support/front_end_commands/table_commands";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const checkIfValidationAppears = (locator) => cy.elementContain(locator, "This field is required")

let defaultCriteriaName, newCriteriaNameUpdated
let indicationSelected, criterionCatSelected, criterionSubCatSelected, parameterSelected, version

Given('The criteria template exists with a status as {string}', (status) => {
    cy.searchAndGetData(status, 'Parent template').then(() => {
        version = objectVersion
        defaultCriteriaName = objectName
    })
})

Given('The Final criteria template exist', () => createAndApproveTemplate())

Given('The Retired criteria template exist', () => {
    createAndApproveTemplate()
    cy.performActionOnSearchedItem('Inactivate')
})

When('The new criteria is added in the library', () => {
    createCriteria()
    cy.searchAndCheckResults(defaultCriteriaName)
})

When('The new Criteria is added in the library with not applicable for indexes', () => {
    defaultCriteriaName = Date.now()
    cy.clickButton('add-template')
    fillNameAndContinue(defaultCriteriaName)
    cy.checkAllCheckboxes()
    cy.clickFormActionButton('save')
})

Then('The new Criteria is visible in the Criteria Templates Table', () => {
    cy.checkRowByIndex(0, 'Parent template', defaultCriteriaName)
    cy.checkStatusAndVersion('Draft', '0.1')
})

Then('The new Criteria is visible with Not Applicable indexes in the Criteria Templates Table', () => {
    cy.checkRowByIndex(0, 'Parent template', defaultCriteriaName)
    cy.checkStatusAndVersion('Draft', '0.1')
})

Then('The updated Criteria is visible within the table', () => {
    cy.searchAndCheckResults(newCriteriaNameUpdated)
    cy.checkRowByIndex(0, 'Parent template', newCriteriaNameUpdated)
    cy.checkStatusAndVersion('Draft', '0.2')
})

When('The new Criteria template is added without template text', () => {
    cy.clickButton('add-template')
    cy.clickFormActionButton('continue')
})

When('The new Criteria template is added without mandatory data', () => {
    cy.clickButton('add-template')
    fillNameAndContinue(Date.now())
    cy.clickFormActionButton('save')
})

Then('The validation appears for Indication or Disorder, Criterion Category, Criterion Sub-Category', () => {
    checkIfValidationAppears('template-indication-dropdown')
    checkIfValidationAppears('template-criterion-category')
    checkIfValidationAppears('template-criterion-sub-category')
})

When('The new template name is prepared with a parameters', () => {
    cy.clickButton('add-template')
    cy.fillTextArea('template-text-field', 'Test [Activity] and [Event] template')
})

When('The syntax is verified', () => cy.clickButton('verify-syntax-button'))

When('The user hides the parameter in the next step', () => {
    cy.clickFormActionButton('continue')
    cy.get('[title^="Show/hide parameter"] .v-btn__content').first().click()
})

When('The user picks the parameter from the dropdown list', () => {
    cy.clickFormActionButton('continue')
    cy.selectLastVSelect("Activity")
    cy.get('[data-cy="Activity"] span').invoke("text").then(text => parameterSelected = text)
})

Then('The parameter is not visible in the text representation', () => checkParameterValue(false, 'Activity'))

Then('The parameter value is visible in the text representation', () => checkParameterValue(true, parameterSelected.split('...')[0]))

When('The created criteria template is edited without change description provided', () => {
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.clearField('template-change-description')
    cy.clickFormActionButton('save')
})

Then('The validation appears for criteria change description field', () => checkIfValidationAppears('template-change-description'))

Then('The criteria is no longer available', () => cy.confirmItemNotAvailable(defaultCriteriaName))

When('The indexing is updated for the Criteria Template', () => {
    fillIndexingData(true)
    cy.clickFormActionButton('save')
})

When('The criteria metadata is updated', () => {
    newCriteriaNameUpdated = `${Date.now()} Updated`
    fillNameAndContinue(newCriteriaNameUpdated)
    fillIndexingData(true)
    cy.clickFormActionButton('continue')
    cy.fillInput('template-change-description', 'updated for test')
    cy.clickFormActionButton('save')
})

Then('The indexes in criteria template are updated', () => {
    cy.wait(2000)
    cy.get('[data-cy="form-body"]').should('contain', indicationSelected)
    cy.get('[data-cy="form-body"]').should('contain', criterionCatSelected)
    cy.get('[data-cy="form-body"]').should('contain', criterionSubCatSelected)
})

Then('The criteria template is updated to draft with version incremented by 0.1', () => cy.checkStatusAndVersion('Draft', version + 0.1))

Then('The template is displayed with a status as Retired with the same version as before', () => cy.checkStatusAndVersion('Retired', version))

Then('The criteria template is displayed with a status as Final with the same version as before', () => cy.checkStatusAndVersion('Final', version))

Then('The status of the criteria template displayed as Final with a version rounded up to full number', () => cy.checkStatusAndVersion('Final', 1))

function createCriteria() {
    defaultCriteriaName = Date.now()
    cy.clickButton('add-template')
    fillNameAndContinue(defaultCriteriaName)
    fillIndexingData(false)
    cy.intercept('/api/criteria-templates?page_number=1&*').as('getCriteria')
    cy.clickFormActionButton('save')
    cy.wait('@getCriteria', {timeout: 20000})
    cy.waitForTable()
}

function fillNameAndContinue(name) {
    cy.fillTextArea('template-text-field', name)
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
}

function fillIndexingData(update) {
    let select = update ? (locator) => cy.selectLastMultipleSelect(locator) : (locator) => cy.selectFirstMultipleSelect(locator)
    cy.clearField('template-indication-dropdown')
    cy.clearField('template-criterion-category')
    cy.clearField('template-criterion-sub-category')
    select('template-indication-dropdown')
    select('template-criterion-category')
    select('template-criterion-sub-category')
    cy.get('[data-cy="template-indication-dropdown"] input').invoke('text').then(text => indicationSelected = text)
    cy.get('[data-cy="template-criterion-category"] input').invoke('text').then(text => criterionCatSelected = text)
    cy.get('[data-cy="template-criterion-sub-category"] input').invoke('text').then(text => criterionSubCatSelected = text)
}

function createAndApproveTemplate() {
    createCriteria()
    cy.searchAndCheckResults(defaultCriteriaName)
    cy.performActionOnSearchedItem('Approve')
}

function checkParameterValue(shouldContain, value) {
    let condition = shouldContain ? 'contain' : 'not.contain'
    cy.get('[edit-mode="false"] .template-readonly').should(condition, value)
    cy.get('[edit-mode="false"] .pa-4').should(condition, value)
}
