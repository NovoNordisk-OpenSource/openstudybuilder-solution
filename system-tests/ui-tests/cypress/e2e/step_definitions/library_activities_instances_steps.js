import { apiActivityName } from "./api_library_steps";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activityInstance, apiActivitInstanceyName, apiTopicCode
let nciconceptid = "NCI-ID", nciname = 'NCI-name', definition = "DEF", adamcode = "Adam-code", topicCode = `Topic${Date.now()}`

When('The Add Activity Instance button is clicked', () => startActivityCreation())

When('The activity instance data is filled in and saved', () => addInstanceAndConfirmCreation(true))

When('The activity instance data with custom activity is filled in and saved', () => addInstanceAndConfirmCreation(false, apiActivityName))

When('The activity instance form is filled with data', () => addInstanceMandatoryData())

When('Second activity instance data is created with the same topic code', () => {
    addInstanceMandatoryData(apiTopicCode)
    cy.clickFormActionButton('save')
})

Then('The newly added Activity Instance item is added in the table by default', () => {
    cy.checkRowByIndex(0, 'Activity Instance', activityInstance)
    cy.checkRowByIndex(0,'Definition', definition)
    cy.checkRowByIndex(0, 'NCI Concept ID', nciconceptid)
    cy.checkRowByIndex(0, 'Topic code', topicCode)
    cy.checkRowByIndex(0, 'ADaM parameter code', adamcode)
    cy.checkRowByIndex(0, 'Required for activity', "Yes")
    cy.checkRowByIndex(0, 'Default selected for activity', "No")
    cy.checkRowByIndex(0, 'Data sharing', "No")
    cy.checkRowByIndex(0, 'Legacy usage', "No")
    cy.checkStatusAndVersion('Draft', '0.1')
})

When('Activity selection is not made', () => cy.clickFormActionButton('continue'))

Then('The validation message appears for Activity field', () => cy.checkIfValidationAppears('instanceform-activity-class'))

Then('The validation message appears for class field', () => cy.checkIfValidationAppears('instanceform-instanceclass-class'))

Then('The validation error for activity in not allowed state is displayed', () => {
    const validationMessage = 'Selected activity is in DRAFT state. Please move the activity to FINAL state before creating the Activity Instance.'
    cy.get('.v-alert__content').should('have.text', validationMessage)
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

When('The Activity created through API is selected', () => {
    fillInstanceActivityGroupData(apiActivityName)
    cy.clickFormActionButton('continue')
})

When('The user fills group and class instance data', () => {
    startActivityCreation()
    fillInstanceGroupAndClassData()
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
    fillInstanceGroupAndClassData()
    cy.clickFormActionButton('save')
})

When('The activity instance is edited', () => {
    activityInstance = apiActivitInstanceyName
    editActivityInstance()
    saveActivityInstance('updated')
})

When('The activity instance edition form is filled with data', () => editActivityInstance())

Then('The activity instance is no longer available', () => cy.confirmItemNotAvailable(apiActivitInstanceyName))

Then('The activity instance is not created', () => cy.confirmItemNotAvailable(activityInstance))

Then('The activity instance is not edited', () => cy.confirmItemNotAvailable(activityInstance))

Then('One activity instance is found after performing full name search', () => cy.searchAndCheckResults(apiActivitInstanceyName))

Then('Activity Instance is found', () => cy.searchFor(apiActivitInstanceyName, false))

Then('Activity instance cannot be saved', () => cy.get('.v-overlay .v-window').should('be.visible'))

When('[API] Activity Instance in status Final with Final group, subgroub and activity linked exists', () => {
    if (!apiActivitInstanceyName) createAndApproveActivityInstanceViaApi()
    cy.getActivityInstanceNameByUid().then(name => apiActivitInstanceyName = name)
})

When('[API] Activity Instance in status Draft exists', () => createActivityInstanceViaApi())

When('[API] Activity Instance is approved', () => cy.approveActivityInstance())

When('[API] Activity Instance is inactivated', () => cy.inactivateActivityInstance())

Given('[API] First activity instance for search test is created', () => createActivityInstanceViaApi(`SearchTest${Date.now()}`))

Given('[API] Second activity instance for search test is created', () => cy.createActivityInstance(`SearchTest${Date.now()}`))

function addInstanceAllData() {
    addInstanceMandatoryData()
    cy.fillInput('instanceform-nciconceptid-field', nciconceptid)
    cy.fillInput('instanceform-nciconceptname-field', nciname)
    cy.fillInput('instanceform-adamcode-field', adamcode)
    cy.get('[data-cy="instanceform-requiredforactivity-checkbox"] input').check()
}

function addInstanceMandatoryData(code = topicCode, customAction = '') {
    activityInstance = `Instance${Date.now()}`
    startActivityCreation()
    fillInstanceGroupAndClassData(customAction)
    cy.fillInput('instanceform-instancename-field', activityInstance)
    cy.fillInput('instanceform-definition-field', definition)
    cy.fillInput('instanceform-topiccode-field', code) 
}

function addInstanceAndConfirmCreation(optionalData = false, customAction = '') {
    optionalData ? addInstanceAllData() : addInstanceMandatoryData(`Topic${Date.now()}`, customAction)
    saveActivityInstance('created')
    cy.wait(2500)
    cy.searchAndCheckResults(activityInstance)
    cy.checkStatusAndVersion('Draft', '0.1')
}

function startActivityCreation() {
    cy.clickButton('add-activity')
    cy.wait(1000)
}

function fillInstanceGroupAndClassData(customActivity = '') {
    fillInstanceActivityGroupData(customActivity)
    cy.selectFirstVSelect('instanceform-instanceclass-dropdown')
    cy.clickFormActionButton('continue')
}

function fillInstanceActivityGroupData(customActivity = '') {
    if (customActivity) cy.get('[data-cy=instanceform-activity-dropdown] input').type(customActivity)
    cy.selectFirstVSelect('instanceform-activity-dropdown')
    cy.get('[data-cy=instanceform-activitygroup-table]').within(() => cy.get('.v-checkbox-btn').first().click())
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

function editActivityInstance() {
    activityInstance = `Update ${activityInstance}`
    cy.get('.v-card-title').should('contain', 'Edit activity instance')
    cy.wait(1000)
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.fillInput('instanceform-instancename-field', activityInstance)
    cy.fillInput('instanceform-definition-field', "update")
}

function createActivityInstanceViaApi(customName = '') {
    cy.intercept('/api/concepts/activities/activity-instances?*').as('getData')
    cy.getFinalGroupUid()
    cy.getFinalSubGroupUid()
    cy.getClassUid()
    cy.createActivity()
    cy.approveActivity()
    cy.createActivityInstance(customName)
    cy.getActivityInstanceNameByUid().then(name => apiActivitInstanceyName = name)
    cy.getActivityInstanceTopicCodeByUid().then(code => apiTopicCode = code)
    cy.wait('@getData', {timeout: 30000})
}

function createAndApproveActivityInstanceViaApi() {
    cy.getClassUid()
    createAndApproveViaApi(() => cy.createGroup(), () => cy.approveGroup())
    createAndApproveViaApi(() => cy.createSubGroup(), () => cy.approveSubGroup())
    createAndApproveViaApi(() => cy.createActivity(), () => cy.approveActivity())
    createAndApproveViaApi(() => cy.createActivityInstance(), () => cy.approveActivityInstance())
}

function createAndApproveViaApi(createFunction, approveFunction) {
    createFunction()
    approveFunction()
}
