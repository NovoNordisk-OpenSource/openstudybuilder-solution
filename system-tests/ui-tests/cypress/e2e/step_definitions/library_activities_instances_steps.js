import { activityName } from "./library_activities_steps";

const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activityInstance
let nciconceptid = "NCI-ID"
let topiccode = "Totic-code"
let definition = "DEF"
let adamcode = "Adam-code"
let approvalConfirmation = 'Activity instance is now in Final state'
let inactivationConfirmation = 'Activity instance inactivated'

When('The Add Activity Instance button is clicked', () => startActivityCreation())

When('The activity instance data is filled in and saved', () => addInstanceDataAndSave())

When('The activity instance form is filled with data', () => addInstanceData())

Given('The test Activity Instance item exists with a status as Draft', () => addInstanceAndConfirmCreation())

Then('The newly added Activity Instance item is added in the table by default', () => {   
    cy.wait(2500)
    cy.searchAndCheckResults(activityInstance)
    cy.checkRowByIndex(0, 'Activity Instance', activityInstance)
    cy.checkRowByIndex(0,'Definition', definition)
    cy.checkRowByIndex(0, 'NCI Concept ID', nciconceptid)
    cy.checkRowByIndex(0, 'Topic code', topiccode)
    cy.checkRowByIndex(0, 'ADaM parameter code', adamcode)
    cy.checkRowByIndex(0, 'Required for activity', "Yes")
    cy.checkRowByIndex(0, 'Default selected for activity', "No")
    cy.checkRowByIndex(0, 'Data sharing', "No")
    cy.checkRowByIndex(0, 'Legacy usage', "No")
    cy.checkStatusAndVersion('Draft', '0.1')
})

When('Activity selection is not made', () => cy.clickFormActionButton('continue'))

Then('The message is displayed as {string} in the Activity field', (message) => {
    cy.warningIsDisplayedForField('[data-cy="instanceform-activity-class"]', message)
})

Then('The message is displayed as {string} in the class field', (message) => {
    cy.warningIsDisplayedForField('[data-cy="instanceform-instanceclass-class"]', message)
})

Then('The message of {string} displayed in all the above mandatory fields', (message) => {
    cy.get('.v-messages__message').should('contain', message)
}) 

When('Activity selected but Activity group does not select', () => {
    cy.selectFirstVSelect('instanceform-activity-dropdown')
    cy.clickFormActionButton('continue')
})

When('The Activity instance class does not select any data', () => {
    fillInstanceActivityGroupData()
    cy.clickFormActionButton('continue')
})

When('The user is editing an activity instance', () => {
    startActivityCreation()
    fillInstanceActivityGroupData()
    fillInstanceClassData()
})

When('The user enters a value for Activity instance name', () => {
    cy.fillInput('instanceform-instancename-field', "TEST")
})

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity instance name', () => {      
    cy.get('[data-cy="sentence-case-name-field"]').within(() => cy.get('input').invoke('val').should('contain', "test"))
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity instance name', () => {
    cy.fillInput('instanceform-instancename-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
    cy.clickFormActionButton('save')
})

Then('The user is not able to save', () => cy.get('[data-cy="save-button"]').should('be.visible'))

Then('The user is not able to continue', () => cy.get('[data-cy="continue-button"]').should('be.visible'))

When('The Activity instance name, Sentence case name, Definition and Topic code fields are not filled with data', () => {
    fillInstanceActivityGroupData()
    fillInstanceClassData()
    cy.clickFormActionButton('save')
})

When('The activity instance is edited', () => {
    editActivityInstance()
    saveActivityInstance('updated')
})

When('The activity instance edition form is filled with data', () => editActivityInstance())

Given('The test Activity Instance item exists with a status as Final', () => {
    addInstanceAndConfirmCreation()
    approveAndConfirmStatus()
})

Given('First activity instance for search test is created', () => addInstanceDataAndSave('SearchTest'))

Given('Second activity instance for search test is created', () => addInstanceDataAndSave('SearchTest'))

Given('The test Activity Instance with status Final and version 1.0 is linked to the test activity', () => {
    addInstanceAndConfirmCreation(activityName)
    approveAndConfirmStatus()
})

Given('The test Activity Instance item exists with a status as Retired', () => {
    addInstanceAndConfirmCreation()
    approveAndConfirmStatus()
    cy.performActionOnSearchedItem('Inactivate', inactivationConfirmation)
    cy.checkStatusAndVersion('Retired', '1.0')
})

Then('The activity instance has status {string} and version {string}', (status, version) => cy.checkStatusAndVersion(status, version))

Then('The activity instance is no longer available', () => cy.confirmItemNotAvailable(activityInstance))

Then('The activity instance is not created', () => cy.confirmItemNotAvailable(activityInstance))

Then('The activity instance is not edited', () => cy.confirmItemNotAvailable(activityInstance))

Then('One activity instance is found after performing full name search', () => cy.searchAndCheckResults(activityInstance))

function addInstanceData(namePrefix = 'Instance') {
    activityInstance = `${namePrefix}${Date.now()}`
    startActivityCreation()
    fillInstanceActivityGroupData(activityName)
    fillInstanceClassData()
    cy.fillInput('instanceform-instancename-field', activityInstance)
    cy.fillInput('instanceform-definition-field', definition)
    cy.fillInput('instanceform-nciconceptid-field', nciconceptid)
    cy.fillInput('instanceform-topiccode-field', topiccode)
    cy.fillInput('instanceform-adamcode-field', adamcode)
    cy.get('[data-cy="instanceform-requiredforactivity-checkbox"] input').check()
}

function addInstanceDataAndSave(namePrefix = 'Instance') {
    addInstanceData(namePrefix)
    saveActivityInstance('created')
}

function addInstanceAndConfirmCreation() {
    addInstanceDataAndSave()
    cy.wait(2500)
    cy.searchAndCheckResults(activityInstance)
    cy.checkStatusAndVersion('Draft', '0.1')
}

function startActivityCreation() {
    cy.clickButton('add-activity', true)
    cy.wait(1000)
}

function fillInstanceActivityGroupData() {
    if(activityName != null) {
        cy.get('[data-cy=instanceform-activity-dropdown] input').type(activityName)
        cy.contains('.v-list-item', activityName).click()
    }
    else cy.selectFirstVSelect('instanceform-activity-dropdown')
    cy.get('[data-cy=instanceform-activitygroup-table]').within(() => cy.get('.v-checkbox-btn').first().click())
    cy.clickFormActionButton('continue')
}

function fillInstanceClassData() {
    cy.selectFirstVSelect('instanceform-instanceclass-dropdown')
    cy.clickFormActionButton('continue')
}

function saveActivityInstance(action) {
    cy.intercept('/api/concepts/activities/activities?*').as('getData')
    cy.intercept('/api/concepts/activities/activity-instances?*').as('getData2')
    cy.clickFormActionButton('save')
    cy.checkSnackbarMessage(`Activity ${action}`)
    cy.wait('@getData', {timeout: 20000})
    cy.wait('@getData2', {timeout: 30000})
}

function approveAndConfirmStatus() {
    cy.performActionOnSearchedItem('Approve', approvalConfirmation)
    cy.checkStatusAndVersion('Final', '1.0')
}

function editActivityInstance() {
    activityInstance = `Update ${activityInstance}`
    cy.get('.v-card-title').should('contain', 'Edit activity instance')
    cy.wait(1000)
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.fillInput('instanceform-instancename-field', activityInstance)
    cy.fillInput('instanceform-definition-field', "update")
}