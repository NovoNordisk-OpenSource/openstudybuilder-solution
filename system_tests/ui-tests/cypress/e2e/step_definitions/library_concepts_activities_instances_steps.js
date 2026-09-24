import { activityInstance_uid } from "../../support/api_requests/library_activities";
import { apiActivityName } from "./api_library_steps";
import { studyActivityInstance } from "./study_define_data_specifications_activity_instances_steps";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let activityInstance, topicCode = `Topic${getShortUniqueId()}`
let nciconceptid = "NCI-ID", nciname = 'NCI-name', adamcode = "Adam-code"

Then('The activity instance groupings has status {string} and version {string}', (status, version) => {
    cy.checkRowByIndex(0, 'Groupings status', status)
    cy.checkRowByIndex(0, 'Groupings version', version)
})

When('User intercepts create instance request', () => cy.intercept('/api/concepts/activities/activity-instances').as('createInstance'))

When('User intercepts update instance request', () => cy.intercept(`/api/concepts/activities/activity-instances/${activityInstance_uid}`).as('updateInstance'))

Then('User waits for activity instance to be created', () => cy.wait('@createInstance', {timeout: 20000}))

Then('User waits for activity instance to be updated', () => cy.wait('@updateInstance', {timeout: 20000}))

When('User waits for edition form to open', () => cy.get('.v-card-title').should('contain', 'Edit activity instance'))

When('The Add Activity Instance button is clicked', () => cy.clickButton('add-activity'))

Then('Activity Instance is searched for and not found', () => cy.searchAndCheckPresence(activityInstance, false))

Then('Activity Instance is searched for and found', () => cy.searchAndCheckPresence(activityInstance, true))

Then('Activity Instance is present in first table row', () => cy.checkRowByIndex(0, 'Activity Instance', activityInstance))

Then('The newly added Activity Instance item is added in the table by default', () => {
    cy.checkRowByIndex(0, 'Activity Instance', activityInstance)
    cy.checkRowByIndex(0, 'NCI Concept ID', nciconceptid)
    cy.checkRowByIndex(0, 'Topic code', topicCode)
    cy.checkRowByIndex(0, 'ADaM parameter code', adamcode)
    cy.checkRowByIndex(0, 'Required for activity', "Yes")
    cy.checkRowByIndex(0, 'Default selected for activity', "No")
    cy.checkRowByIndex(0, 'Data sharing', "No")
    cy.checkRowByIndex(0, 'Legacy usage', "No")
})

Then('The validation message appears for Activity field', () => cy.checkIfValidationAppears('instanceform-activity-class'))

Then('The validation message appears for class field', () => cy.checkIfValidationAppears('instanceform-instanceclass-class'))

Then('The validation message appears for activity instance name field', () => cy.checkIfValidationAppears('instanceform-instancename-field'))

Then('The validation message appears for definition field', () => cy.checkIfValidationAppears('instanceform-definition-field'))

Then('The validation message appears for topic code field', () => cy.checkIfValidationAppears('instanceform-topiccode-field'))

Then('The validation error for {string} activity in not allowed state is displayed when {string} instance', (status, action) => {
    const validationMessage = `Selected activity is in ${status.toUpperCase()} state. Please move the activity to FINAL state before ${action} the Activity Instance.`
    cy.get('.v-alert__content').should('have.text', validationMessage)
})

When('The Activity instance activity is selected', () => cy.selectFirstVSelect('instanceform-activity-dropdown'))

When('The Activity instance group data is filled in', () => fillInstanceActivityGroupData())

When('The Activity instance group data is filled in with activity created via API', () => fillInstanceActivityGroupData(apiActivityName))

When('The Activity instance class data is filled in', () => cy.selectFirstVSelect('instanceform-instanceclass-dropdown'))

When('The Activity instance mandatory data is filled in', () => fillInstanceMandatoryData())

When('The Activity instance optional data is filled in', () => fillInstanceOptionalData())

When('The user enters a value for Activity instance name', () => cy.fillInput('instanceform-instancename-field', "TEST"))

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity instance name', () => {      
    cy.get('[data-cy="sentence-case-name-field"]').within(() => cy.get('input').invoke('val').should('contain', "test"))
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity instance name', () => {
    cy.fillInput('instanceform-instancename-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
})

When('The user updates instance name', () => {
    activityInstance = `Update ${activityInstance}`
    cy.fillInput('instanceform-instancename-field', activityInstance)
})

Then('The user is not able to save', () => cy.get('[data-cy="save-button"]').should('be.visible'))

Then('The user is not able to continue', () => cy.get('[data-cy="continue-button"]').should('be.visible'))

Then('Linked Activity group and subgroup are loaded', () => cy.get('[data-cy="instanceform-activitygroup-table"]').should('be.visible'))

When('[API] Activity Instance in status Final with Final group, subgroup and activity linked exists', () => {
    if (!activityInstance) createAndApproveActivityInstanceViaApi()
    cy.getActivityInstanceNameByUid().then(name => activityInstance = name)
})

When('[API] Activity Instance is created and approved', () => { cy.createActivityInstance(), cy.approveActivityInstance()})

When('[API] Get class uid for activity instance creation', () => cy.getClassUid())

When('[API] Activity Instance in status Draft exists', () => createActivityInstanceViaApi())

When('[API] Activity Instance is approved', () => cy.approveActivityInstance())

When('[API] Activity Instance is inactivated', () => cy.inactivateActivityInstance())

When('[API] User gets uid of study activity instance with name saved in previous step', () => cy.getInstanceUidByName(studyActivityInstance))

When('[API] Activity Instance new version is created', () => cy.activityInstanceNewVersion())

Given('[API] First activity instance for search test is created', () => createActivityInstanceViaApi(`SearchTest${getShortUniqueId()}`))

Given('[API] Second activity instance for search test is created', () => cy.createActivityInstance(`SearchTest${getShortUniqueId()}`))

Then('[API] Activity instance is updated with new name', () => cy.updateActivityInstanceAttributes(`New Activity Instance name ${getShortUniqueId()}`))

Then('[API] Activity instance is updated with new name {string}', (name) => cy.updateActivityInstanceAttributes(`${name}_${getShortUniqueId()}`))

function fillInstanceMandatoryData(code = topicCode) {
    activityInstance = `Instance${getShortUniqueId()}`
    cy.fillInput('instanceform-instancename-field', activityInstance)
    cy.fillInput('instanceform-definition-field', 'DEF')
    cy.fillInput('instanceform-topiccode-field', code) 
}

function fillInstanceOptionalData() {
    cy.fillInput('instanceform-nciconceptid-field', nciconceptid)
    cy.fillInput('instanceform-nciconceptname-field', nciname)
    cy.fillInput('instanceform-adamcode-field', adamcode)
    cy.get('[data-cy="instanceform-requiredforactivity-checkbox"] input').check()
}

function fillInstanceActivityGroupData(customActivity = '') {
    if (customActivity) cy.get('[data-cy=instanceform-activity-dropdown] input').type(customActivity)
    cy.selectFirstVSelect('instanceform-activity-dropdown')
    cy.get('[data-cy=instanceform-activitygroup-table]').within(() => cy.get('.v-checkbox-btn').first().click())
}

function createActivityInstanceViaApi(customName = '') {
    cy.getFinalGroupUid()
    cy.getFinalSubGroupUid()
    cy.getClassUid()
    cy.createActivity()
    cy.approveActivity()
    cy.createActivityInstance(customName)
    cy.getActivityInstanceNameByUid().then(name => activityInstance = name)
    cy.getActivityInstanceTopicCodeByUid().then(code => topicCode = code)
}

function createAndApproveActivityInstanceViaApi() {
    cy.getClassUid()
    cy.createGroup(), cy.approveGroup()
    cy.createSubGroup(), cy.approveSubGroup()
    cy.createActivity(), cy.approveActivity()
    cy.createActivityInstance(), cy.approveActivityInstance()
}